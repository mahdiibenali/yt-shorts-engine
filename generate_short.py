"""Unified video generation module for YouTube Shorts.

Consolidates the boilerplate from individual run_*.py scripts into a single
reusable ``generate_short`` coroutine and a synchronous ``run`` wrapper.
"""

import asyncio
import io
import logging
import os

import numpy as np
from PIL import Image

# --- Safe MoviePy imports (v1 / v2 compatibility) ---
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip,
    )
except ImportError:
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip,
    )

from app.audio.tts import TTSEngine
from app.video.captions import CaptionGenerator
from app.render.composer import VideoComposer
from app.video.image_providers import generate_image
from app.video.director.director_engine import DirectorPlanner
from app.video.director.world_state import GlobalStyleBible, EpisodeWorld, CharacterSheet
from app.video.director.director_coach import DirectorCoach, DirectorMemory
from app.video.director.prompt_translator import PromptTranslator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clip_set(clip, method_v2: str, method_v1: str, value):
    """Call the MoviePy v2 method if available, otherwise fall back to v1."""
    if hasattr(clip, method_v2):
        return getattr(clip, method_v2)(value)
    return getattr(clip, method_v1)(value)


def _save_valid_image(data: bytes, output_path: str, width: int, height: int) -> bool:
    """Write *data* to *output_path*, normalized to width x height via a
    center crop + resize; return False when it is not a decodable image."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
    except Exception:
        return False

    tw, th = width, height
    src_ratio = img.width / img.height
    tgt_ratio = tw / th
    if src_ratio > tgt_ratio:
        new_w = round(img.height * tgt_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = round(img.width / tgt_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    img = img.resize((tw, th), Image.LANCZOS)

    with open(output_path, "wb") as f:
        img.save(f, format="JPEG", quality=92)
    return True


def _download_image(
    prompt: str,
    output_path: str,
    width: int = 1080,
    height: int = 960,
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
) -> str:
    """Generate an image via the configured provider chain (DashScope, then
    Pollinations-with-token), skipping if already cached."""
    if os.path.exists(output_path):
        logger.info("Image already cached: %s", output_path)
        return output_path

    print(f"Generating image for: {prompt[:50]}...")

    last_err = None
    for candidate in (prompt, "3d cartoon neon colorful detailed 8k"):
        try:
            data = generate_image(candidate[:300], width, height)
            if data and _save_valid_image(data, output_path, width, height):
                return output_path
        except Exception as e:
            last_err = e
            logger.warning("Image provider failed: %s", e)

    raise RuntimeError(f"Failed to generate image (provider chain exhausted): {last_err}")


def _loop_gameplay(gameplay, duration: float):
    """Loop a gameplay clip to fill *duration*, with v1/v2 fallbacks."""
    if gameplay.duration >= duration:
        return _clip_set(gameplay, "with_duration", "set_duration", duration)

    if hasattr(gameplay, "with_effects"):
        try:
            from moviepy.video.fx.Loop import Loop
            return gameplay.with_effects([Loop(duration=duration)])
        except ImportError:
            pass
        try:
            import moviepy.video.fx.all as vfx
            return gameplay.with_effects([vfx.loop(duration=duration)])
        except ImportError:
            pass

    if hasattr(gameplay, "loop"):
        return gameplay.loop(duration=duration)

    try:
        from moviepy.video.fx.loop import loop as gloop
        return gloop(gameplay, duration=duration)
    except ImportError:
        pass

    # Last resort — just clamp
    return _clip_set(gameplay, "with_duration", "set_duration", duration)


def _compute_caption_y(position: str, total_height: int, canvas_h: int = 1920) -> int:
    """Return the top y-coordinate for the caption block."""
    if position == "bottom":
        return canvas_h - total_height - 200
    if position == "top":
        return 200
    # "center" or anything else
    return (canvas_h - total_height) // 2


def _normalize_word(word: str) -> str:
    return (word or "").lower().replace("'", "").strip().rstrip(".,!?;:-")


def _find_reveal_time(segs, reveal_word: str | None, duration: float, fallback_frac: float = 0.8) -> float:
    """Start time of the spoken reveal word/phrase, else a fraction of duration.

    Searches the Whisper word timings for *reveal_word* (a phrase may span
    several word tokens).  When the phrase is missing entirely it falls back to
    ``fallback_frac`` of the video so the reveal still lands near the end.
    """
    if not reveal_word or not segs:
        return duration * fallback_frac
    tokens = [t for t in _normalize_word(reveal_word).split() if t]
    words = []
    for seg in segs:
        for w in seg.words or [{"word": seg.text, "start": seg.start, "end": seg.end}]:
            words.append(w)
    if not words or not tokens:
        return duration * fallback_frac
    norms = [_normalize_word(w.get("word", "")) for w in words]
    candidates = [
        i
        for i in range(len(norms) - len(tokens) + 1)
        if norms[i:i + len(tokens)] == tokens
    ]
    if not candidates:
        return duration * fallback_frac
    mid = len(words) // 2
    late = [c for c in candidates if c >= mid]
    idx = (late or candidates)[-1]
    return float(words[idx]["start"])


def _find_countdown_time(segs, max_gap: float = 2.0) -> float | None:
    """Start time of the final ``one``/``1`` in the countdown.

    Looks for the last ``three ... two ... one`` (or ``3 2 1``) run of word
    tokens with each consecutive step within *max_gap* seconds, and returns
    the start of the final ``one`` — the exact moment the countdown completes.
    Returns ``None`` when no countdown is detected.
    """
    words = []
    for seg in segs:
        for w in seg.words or [{"word": seg.text, "start": seg.start, "end": seg.end}]:
            words.append(w)
    if len(words) < 3:
        return None
    code = []
    for w in words:
        n = _normalize_word(w.get("word", "")).strip("0")
        if n in ("three", "3"):
            code.append("3")
        elif n in ("two", "2"):
            code.append("2")
        elif n in ("one", "1"):
            code.append("1")
        else:
            code.append("")
    best = None
    for i in range(len(code) - 2):
        if code[i] == "3" and code[i + 1] == "2" and code[i + 2] == "1":
            g1 = words[i + 1]["start"] - words[i]["start"]
            g2 = words[i + 2]["start"] - words[i + 1]["start"]
            if g1 < max_gap and g2 < max_gap:
                best = float(words[i + 2]["start"])
    return best


def _build_reveal_clip(reveal_path: str, start: float, duration: float,
                       canvas_w: int, canvas_h: int, half_h: int,
                       is_split_screen: bool, zoom: bool = True):
    """Build the real-photo reveal clip (top-half in split-screen, else full-screen).

    Applies a slow Ken Burns push-in so the reveal never feels like a frozen
    screenshot.  The image is cover-cropped to its display region first.
    """
    from moviepy import ImageClip
    from PIL import Image as PILImage

    base_w, base_h = (canvas_w, half_h) if is_split_screen else (canvas_w, canvas_h)
    pil_img = PILImage.open(reveal_path).convert("RGB")
    w, h = pil_img.size
    target_ar = base_w / base_h
    src_ar = w / h
    if src_ar > target_ar:
        new_w = int(h * target_ar)
        x0 = (w - new_w) // 2
        pil_img = pil_img.crop((x0, 0, x0 + new_w, h))
    elif src_ar < target_ar:
        new_h = int(w / target_ar)
        y0 = (h - new_h) // 2
        pil_img = pil_img.crop((0, y0, w, y0 + new_h))
    arr = np.array(pil_img.resize((base_w, base_h)))

    clip = ImageClip(arr)
    if zoom:
        z = lambda t: 1 + 0.15 * (t / duration)  # noqa: E731
        pos_fn = lambda t: ((canvas_w - base_w * z(t)) / 2, (base_h - base_h * z(t)) / 2)  # noqa: E731
        try:
            clip = clip.resized(z).with_position(pos_fn)
        except AttributeError:
            clip = clip.resize(z).set_position(pos_fn)
    else:
        pos = ("center", "top") if is_split_screen else "center"
        try:
            clip = clip.with_position(pos)
        except AttributeError:
            clip = clip.set_position(pos)
    clip = _clip_set(clip, "with_duration", "set_duration", duration)
    clip = _clip_set(clip, "with_start", "set_start", start)
    return clip


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_short(
    script: str,
    image_prompts: list[str],
    output_path: str,
    voice: str = "en-GB-RyanNeural",
    gameplay_path: str | None = None,
    font_size: int = 60,
    highlight_color: tuple = (255, 215, 0, 255),
    caption_position: str = "center",
    image_width: int = 1080,
    image_height: int = 960,
    data_dir: str | None = None,
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    experiment_id: int | None = None,
    entity: str | None = None,
    channel: str | None = None,
    hook: str | None = None,
    record: bool = True,
    graph_db: str | None = None,
    reveal_word: str | None = None,
    reveal_search: str | None = None,
    reveal_image: str | None = None,
    reveal_zoom: bool = True,
) -> str:
    """Generate a YouTube Short from a narration script and image prompts.

    Parameters
    ----------
    script:
        The narration text that will be converted to speech.
    image_prompts:
        One Pollinations AI prompt per scene.  The audio duration is split
        evenly across all prompts.
    output_path:
        Destination path for the final MP4.
    voice:
        Edge TTS voice identifier.
    gameplay_path:
        Optional path to a gameplay video.  When provided, the short uses a
        split-screen layout (AI images on top, gameplay on bottom, each
        1080×960).  When *None*, images are rendered full-screen (1080×1920)
        and ``image_height`` is automatically set to 1920.
    font_size:
        Font size for captions.
    highlight_color:
        RGBA tuple for the highlighted (active) caption word.
    caption_position:
        Vertical placement of the caption block — ``"center"``, ``"top"``,
        or ``"bottom"``.
    image_width:
        Width of each generated image (default 1080).
    image_height:
        Height of each generated image.  Automatically adjusted to 1920 for
        full-screen mode when no *gameplay_path* is given.
    data_dir:
        Directory for intermediate files (audio, scene images).  When *None*,
        derived from the *output_path* basename
        (e.g. ``"CRITTER_WHALE.mp4"`` → ``"data/critter_whale"``).
    user_agent:
        User-Agent header sent with Pollinations requests.
    reveal_word:
        The spoken reveal name (e.g. ``"sea otter"``).  When combined with a
        real reveal photo, the last AI scene is replaced by the photo exactly
        at this word's timestamp.
    reveal_search:
        Common name used to find a trusted Wikimedia Commons photo for the
        reveal (keyless, quality-curated search).
    reveal_image:
        Optional local path to a reveal photo, bypassing Commons search.
    reveal_zoom:
        Whether to apply a slow Ken Burns push-in on the reveal photo.

    Returns
    -------
    str
        The *output_path* of the rendered video.
    """

    # --- Resolve data directory -------------------------------------------
    if data_dir is None:
        base = os.path.splitext(os.path.basename(output_path))[0].lower()
        data_dir = os.path.join("data", base)
    os.makedirs(data_dir, exist_ok=True)

    # If no gameplay video, switch to full-screen images
    is_split_screen = gameplay_path is not None and os.path.exists(gameplay_path)
    if not is_split_screen:
        image_height = 1920

    canvas_w, canvas_h = 1080, 1920
    half_h = 960  # height of each half in split-screen mode

    # ------------------------------------------------------------------
    # 0. AI Film Director Planning & Storyboarding (Production Mode)
    # ------------------------------------------------------------------
    if not image_prompts or len(image_prompts) == 0:
        print("🎬 AI Film Director: Planning storyboard from narration script...")
        topic_name = entity or os.path.splitext(os.path.basename(output_path))[0].replace("CRITTER_", "").replace("_", " ").title()
        style_bible = GlobalStyleBible()
        hero_char = CharacterSheet(
            name=topic_name,
            species=topic_name,
            primary_features=f"Chubby cute {topic_name}, vibrant natural textures, dark expressive eyes",
            color_palette="Warm organic tones",
            personality_vibe="Curious and friendly"
        )
        world = EpisodeWorld(
            episode_id=os.path.splitext(os.path.basename(output_path))[0],
            topic_name=topic_name,
            environment_anchor=f"Natural vibrant habitat for {topic_name}",
            lighting_anchor="Golden hour backlight with soft ambient fill",
            weather_atmosphere="Atmospheric morning mist with soft floating particles",
            hero_character=hero_char,
            recurring_motifs=["Golden sun rays", "Nature foliage bokeh"]
        )
        planner = DirectorPlanner(style_bible=style_bible)
        lines = [s.strip() for s in script.split(".") if s.strip()]
        storyboard = []
        total_lines = len(lines)
        scene_idx = 1
        for line in lines:
            beats = planner.dissect_into_semantic_beats(line)
            for b_idx, beat in enumerate(beats):
                spec = planner.plan_scene_specification(scene_idx, b_idx, beat, world, total_scenes=total_lines)
                storyboard.append(spec)
            scene_idx += 1

        coach = DirectorCoach()
        audit = coach.audit_storyboard(storyboard)
        print(f"🧠 Director Storyboard Audit Score: {audit.sequence_score}/10 (Passed: {audit.passed})")

        memory = DirectorMemory()
        memory.log_storyboard(world.episode_id, storyboard, audit)

        translator = PromptTranslator(style_bible=style_bible)
        image_prompts = [translator.translate_to_pollinations_prompt(spec) for spec in storyboard]
        print(f"🎬 Directed {len(image_prompts)} cinematic shots for render.")

    # ------------------------------------------------------------------
    # 1. Download scene images
    # ------------------------------------------------------------------
    print("Downloading scene images...")
    for i, prompt in enumerate(image_prompts):
        img_path = os.path.join(data_dir, f"scene_{i}.jpg")
        _download_image(
            prompt, img_path,
            width=image_width, height=image_height,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------------
    # 2. Generate TTS audio
    # ------------------------------------------------------------------
    print("Generating TTS...")
    tts = TTSEngine()
    audio_path = os.path.join(data_dir, "voice.mp3")
    await tts.generate(script, audio_path, voice=voice)
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # ------------------------------------------------------------------
    # 3. Generate word-level captions via Whisper
    # ------------------------------------------------------------------
    print("Generating captions...")
    caps = CaptionGenerator()
    segs = caps.generate(audio_path)
    segs = caps.correct_spellings(segs, script)

    # ------------------------------------------------------------------
    # 3b. Resolve a real-photo reveal (Wikimedia Commons) if requested
    # ------------------------------------------------------------------
    reveal_path = None
    reveal_meta = None
    if reveal_image and os.path.exists(reveal_image):
        reveal_path = reveal_image
    elif reveal_search:
        try:
            from app.video import reveal_images
            reveal_path, reveal_meta = reveal_images.resolve_and_download(
                reveal_search,
                [reveal_search.lower(), *_normalize_word(reveal_word).split()],
                data_dir,
            )
        except Exception as e:
            logger.warning("Reveal photo resolution skipped: %s", e)
    if reveal_path:
        print(f"🎉 Real-photo reveal active: {reveal_path}")

    # ------------------------------------------------------------------
    # 4. Build scene image clips
    # ------------------------------------------------------------------
    print("Building scene clips...")
    image_clips = []
    n_prompts = len(image_prompts)

    reveal_time = None
    if reveal_path:
        reveal_time = _find_countdown_time(segs)
        if reveal_time is None:
            reveal_time = _find_reveal_time(segs, reveal_word, duration)
        # keep the real reveal inside a sane window: at least half-way and with
        # ~2s on screen
        reveal_time = min(max(reveal_time, duration * 0.5), duration - 2.0)
        if duration - reveal_time < 1.5 or duration < 4.0:
            reveal_time = None

    if reveal_time is not None:
        n_pre = max(1, n_prompts - 1)
        prompts_to_use = image_prompts[:n_pre]
        clip_duration = reveal_time / n_pre
    else:
        prompts_to_use = image_prompts
        clip_duration = duration / n_prompts

    for i, prompt in enumerate(prompts_to_use):
        img_path = os.path.join(data_dir, f"scene_{i}.jpg")
        target_size = (image_width, half_h) if is_split_screen else (canvas_w, canvas_h)
        pil_img = Image.open(img_path).convert("RGB").resize(target_size)
        img_clip = ImageClip(np.array(pil_img))

        img_clip = _clip_set(img_clip, "with_duration", "set_duration", clip_duration)
        img_clip = _clip_set(img_clip, "with_start", "set_start", i * clip_duration)

        if is_split_screen:
            img_clip = _clip_set(img_clip, "with_position", "set_position", ("center", "top"))
        else:
            img_clip = _clip_set(img_clip, "with_position", "set_position", "center")

        image_clips.append(img_clip)

    if reveal_time is not None:
        reveal_clip = _build_reveal_clip(
            reveal_path, reveal_time, duration - reveal_time,
            canvas_w, canvas_h, half_h, is_split_screen, reveal_zoom,
        )
        image_clips.append(reveal_clip)

    # ------------------------------------------------------------------
    # 5. Build gameplay / bottom-half clip (split-screen only)
    # ------------------------------------------------------------------
    if is_split_screen:
        print("Adding gameplay video (split-screen bottom half)...")
        gameplay = VideoFileClip(gameplay_path)
        gameplay = _loop_gameplay(gameplay, duration)

        gameplay = _clip_set(gameplay, "resized", "resize", (image_width, half_h))
        gameplay = _clip_set(gameplay, "with_position", "set_position", ("center", "bottom"))
        gameplay = _clip_set(gameplay, "with_duration", "set_duration", duration)

        base_clips = [gameplay] + image_clips
    else:
        base_clips = image_clips

    # ------------------------------------------------------------------
    # 6. Composite background + audio
    # ------------------------------------------------------------------
    print("Compositing background...")
    bg_video = CompositeVideoClip(base_clips, size=(canvas_w, canvas_h))
    bg_video = _clip_set(bg_video, "with_audio", "set_audio", audio)
    bg_video = _clip_set(bg_video, "with_duration", "set_duration", duration)

    # ------------------------------------------------------------------
    # 7. Render caption overlay clips
    # ------------------------------------------------------------------
    print("Rendering captions...")
    composer = VideoComposer()
    font = composer._get_font(font_size)
    caption_clips = []

    for seg in segs:
        words = seg.words or [{"word": seg.text, "start": seg.start, "end": seg.end}]
        lines, total_height, space_w, line_spacing = composer._layout_words(words, font)
        start_y = _compute_caption_y(caption_position, total_height, canvas_h)

        for w in words:
            w_dur = w["end"] - w["start"]
            if w_dur <= 0:
                w_dur = 0.15

            pil_img = composer._render_caption_image(
                lines, w, font,
                start_y=start_y,
                line_spacing=line_spacing,
                space_w=space_w,
                bg_box=True,
                highlight_color=highlight_color,
            )

            img_arr = np.array(pil_img)
            txt_clip = ImageClip(img_arr[:, :, :3])

            try:
                mask_clip = ImageClip(img_arr[:, :, 3] / 255.0, ismask=True)
            except TypeError:
                mask_clip = ImageClip(img_arr[:, :, 3] / 255.0)

            if hasattr(txt_clip, "with_mask"):
                txt_clip = (
                    txt_clip
                    .with_mask(mask_clip)
                    .with_start(w["start"])
                    .with_duration(w_dur)
                    .with_position("center")
                )
            else:
                txt_clip = (
                    txt_clip
                    .set_mask(mask_clip)
                    .set_start(w["start"])
                    .set_duration(w_dur)
                    .set_position("center")
                )

            caption_clips.append(txt_clip)

    # ------------------------------------------------------------------
    # 8. Final composite & write
    # ------------------------------------------------------------------
    print("Writing final video...")
    final = CompositeVideoClip([bg_video] + caption_clips, size=(canvas_w, canvas_h))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="medium",
        threads=4,
        logger=None,
    )

    # ------------------------------------------------------------------
    # 9. Record the video into the Curiosity knowledge graph
    # ------------------------------------------------------------------
    if record:
        try:
            from curiosity.features import extract_features
            from curiosity.graph import GraphStore

            image_paths = [
                os.path.join(data_dir, f"scene_{i}.jpg")
                for i in range(len(prompts_to_use))
            ]
            if reveal_path:
                image_paths.append(reveal_path)
            styling = {
                "voice": voice,
                "highlight_color": tuple(highlight_color),
                "caption_position": caption_position,
                "split_screen": is_split_screen,
                "font_size": font_size,
                "scene_count": len(image_prompts),
                "duration": duration,
                "reveal": "real_photo" if reveal_path else None,
                "reveal_zoom": reveal_zoom if reveal_path else None,
                "reveal_license": (reveal_meta or {}).get("license") if reveal_path else None,
            }
            feats = extract_features(script, segs, duration, image_paths, styling)
            store = GraphStore(graph_db) if graph_db else GraphStore()
            store.record_video(
                video_name=os.path.basename(output_path),
                features=feats,
                script=script,
                entity=entity,
                channel=channel,
                hook=hook,
                extra_payload={
                    "image_prompts": image_prompts,
                    "gameplay_path": gameplay_path,
                    "reveal_photo": reveal_path,
                    "reveal_meta": reveal_meta or {},
                },
                experiment_id=experiment_id,
            )
            store.close()
        except Exception as e:
            logger.warning("Curiosity feature recording skipped: %s", e)

    # Clean up
    final.close()
    bg_video.close()
    audio.close()
    for c in caption_clips:
        if hasattr(c, "close"):
            c.close()

    print(f"DONE! Saved to {output_path}")
    return output_path


def run(script: str, image_prompts: list[str], output_path: str, **kwargs) -> str:
    """Synchronous wrapper around :func:`generate_short`."""
    return asyncio.run(generate_short(script, image_prompts, output_path, **kwargs))
