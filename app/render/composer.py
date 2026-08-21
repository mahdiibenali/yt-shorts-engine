import os
import random
import logging
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.video.captions import CaptionSegment

logger = logging.getLogger(__name__)

# --- Safe MoviePy Imports & Wrappers for v1 and v2 compatibility ---
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        ImageClip, ColorClip, CompositeAudioClip
    )
    import moviepy.video.fx as vfx
except ImportError:
    try:
        from moviepy import (
            VideoFileClip, AudioFileClip, CompositeVideoClip,
            ImageClip, ColorClip, vfx
        )
        from moviepy.audio.AudioClip import CompositeAudioClip
    except ImportError as e:
        logger.error(f"Failed to import MoviePy components: {e}")
        raise

def safe_subclip(clip, start, end):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)

def safe_resize(clip, size):
    if hasattr(clip, "resized"):
        return clip.resized(size)
    return clip.resize(size)

def safe_with_audio(clip, audio):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    return clip.set_audio(audio)

def safe_with_start(clip, start):
    if hasattr(clip, "with_start"):
        return clip.with_start(start)
    return clip.set_start(start)

def safe_with_duration(clip, duration):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)

def safe_with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)

def safe_volume(clip, factor):
    if hasattr(clip, "multiply_volume"):
        return clip.multiply_volume(factor)
    if hasattr(clip, "volumex"):
        return clip.volumex(factor)
    return clip

@dataclass
class CompositionConfig:
    background_video_path: str
    audio_path: str
    captions: List[CaptionSegment]
    output_path: str
    duration: float
    caption_position: str = "bottom"
    caption_bg_color: str = "black"
    font_size: int = 48
    music_path: Optional[str] = None
    music_volume: float = 0.12
    padding_back: float = 1.0
    gameplay_video_path: Optional[str] = None


class VideoComposer:
    def __init__(self):
        self.temp_dir = os.path.join(settings.temp_dir, "render")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _get_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """Finds a valid font path, falling back to system fonts if Roboto is missing."""
        font_paths = [
            os.path.join(settings.data_dir, "..", "app", "assets", "fonts", "Roboto-Bold.ttf"),
            "C:\\Windows\\Fonts\\arialbd.ttf",  # Windows Arial Bold
            "C:\\Windows\\Fonts\\arial.ttf",    # Windows Arial
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # MacOS
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, font_size)
                except Exception:
                    continue
        logger.warning("Could not load any custom font, using PIL default font.")
        return ImageFont.load_default()

    def _layout_words(self, words: List[Dict], font: ImageFont.FreeTypeFont, max_width: int = 900) -> tuple:
        """Computes structural layout (lines) for word wrapping."""
        # Setup temporary draw context to measure word widths
        dummy_img = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        # Measure standard spaces
        space_bbox = draw.textbbox((0, 0), " ", font=font)
        space_w = space_bbox[2] - space_bbox[0]

        word_dims = []
        for w_obj in words:
            w_text = w_obj["word"]
            bbox = draw.textbbox((0, 0), w_text, font=font)
            w_w = bbox[2] - bbox[0]
            w_h = bbox[3] - bbox[1]
            word_dims.append({"text": w_text, "w": w_w, "h": w_h, "obj": w_obj})

        lines = []
        current_line = []
        current_width = 0

        for wd in word_dims:
            # Check if adding the word exceeds max_width
            if current_line and current_width + space_w + wd["w"] > max_width:
                lines.append((current_line, current_width))
                current_line = [wd]
                current_width = wd["w"]
            else:
                if current_line:
                    current_width += space_w
                current_line.append(wd)
                current_width += wd["w"]

        if current_line:
            lines.append((current_line, current_width))

        line_spacing = int(font.size * 1.3)
        total_height = len(lines) * line_spacing

        return lines, total_height, space_w, line_spacing

    def _render_caption_image(self, lines: list, active_word_obj: dict, font: ImageFont.FreeTypeFont,
                              canvas_w: int = 1080, canvas_h: int = 1920, start_y: int = 1400,
                              line_spacing: int = 65, space_w: int = 12, highlight_color: tuple = (255, 215, 0, 255),
                              stroke_color: tuple = (0, 0, 0, 255), stroke_width: int = 4, bg_box: bool = True) -> Image.Image:
        """Renders an RGBA subtitle card where only the active word is highlighted."""
        img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        y = start_y
        for line_words, line_w in lines:
            x = (canvas_w - line_w) // 2

            if bg_box:
                line_h = font.size * 1.2
                # Draw semi-transparent dark container behind words for high contrast
                draw.rectangle(
                    [x - 15, y - 5, x + line_w + 15, y + line_h + 5],
                    fill=(0, 0, 0, 140)
                )

            for wd in line_words:
                is_active = (wd["obj"] == active_word_obj)
                color = highlight_color if is_active else (255, 255, 255, 255)

                draw.text(
                    (x, y),
                    wd["text"],
                    font=font,
                    fill=color,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_color
                )
                x += wd["w"] + space_w
            y += line_spacing

        return img

    def compose(self, cfg: CompositionConfig) -> str:
        # Load or create background clip
        if not cfg.background_video_path or not os.path.exists(cfg.background_video_path):
            background = ColorClip(size=(1080, 1920), color=(20, 20, 30))
            background = safe_with_duration(background, cfg.duration)
            logger.info("No valid background video path provided. Using solid color background.")
        elif cfg.background_video_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
            # Static image background (e.g. from Pollinations AI image generator)
            logger.info(f"Using static image as background: {cfg.background_video_path}")
            bg_image = Image.open(cfg.background_video_path).convert("RGB").resize((1080, 1920))
            bg_array = np.array(bg_image)
            background = ImageClip(bg_array)
            background = safe_with_duration(background, cfg.duration)
        else:
            background = VideoFileClip(cfg.background_video_path)

            # Loop or trim background video to match audio length
            if background.duration < cfg.duration:
                if hasattr(background, "with_effects"):
                    try:
                        # moviepy 2.x
                        from moviepy.video.fx.Loop import Loop
                        background = background.with_effects([
                            Loop(duration=cfg.duration)
                        ])
                    except ImportError:
                        try:
                            # older moviepy v2 alpha
                            import moviepy.video.fx.all as vfx
                            background = background.with_effects([
                                vfx.loop(duration=cfg.duration)
                            ])
                        except ImportError:
                            pass
                elif hasattr(background, "loop"):
                    background = background.loop(duration=cfg.duration)
                else:
                    try:
                        from moviepy.video.fx.loop import loop
                        background = loop(background, duration=cfg.duration)
                    except ImportError:
                        # Fallback for v2 if loop effect is somewhere else or not available
                        import moviepy.video.fx as vfx
                        if hasattr(vfx, "Loop"):
                            background = background.with_effects([vfx.Loop(duration=cfg.duration)])
                        else:
                            background = background.with_effects([vfx.loop(duration=cfg.duration)])
            else:
                start = random.uniform(0, max(0.0, background.duration - cfg.duration))
                background = safe_subclip(background, start, start + cfg.duration)

            background = safe_resize(background, (1080, 1920))

        # --- Handle Gameplay Split Screen (Sludge content style) ---
        if cfg.gameplay_video_path and os.path.exists(cfg.gameplay_video_path):
            try:
                gameplay_clip = VideoFileClip(cfg.gameplay_video_path)
                
                # Loop or trim gameplay video
                if gameplay_clip.duration < cfg.duration:
                    if hasattr(gameplay_clip, "loop"):
                        gameplay_clip = gameplay_clip.loop(duration=cfg.duration)
                    else:
                        from moviepy.video.fx.loop import loop as gloop
                        gameplay_clip = gloop(gameplay_clip, duration=cfg.duration)
                else:
                    g_start = random.uniform(0, max(0.0, gameplay_clip.duration - cfg.duration))
                    gameplay_clip = safe_subclip(gameplay_clip, g_start, g_start + cfg.duration)
                
                # Resize both to 1080x960 (half screen)
                background = safe_resize(background, (1080, 960))
                gameplay_clip = safe_resize(gameplay_clip, (1080, 960))
                
                # Position them
                background = safe_with_position(background, ("center", "top"))
                gameplay_clip = safe_with_position(gameplay_clip, ("center", "bottom"))
                
                # Combine them into a new background
                background = CompositeVideoClip([background, gameplay_clip], size=(1080, 1920))
                background = safe_with_duration(background, cfg.duration)
                logger.info(f"Applied split screen with gameplay video: {cfg.gameplay_video_path}")
            except Exception as e:
                logger.error(f"Failed to add gameplay video: {e}")

        narration = AudioFileClip(cfg.audio_path)

        # Load font
        font = self._get_font(cfg.font_size)

        # Build dynamic caption overlays using Pillow (Independent of ImageMagick)
        caption_clips = []
        for seg in cfg.captions:
            # Handle text segments with word timings
            words = seg.words
            if not words:
                # Fallback if no word timings: treat entire segment text as one single block
                words = [{"word": seg.text, "start": seg.start, "end": seg.end}]

            # Determine layout structure for the whole phrase
            lines, total_height, space_w, line_spacing = self._layout_words(words, font)

            # Center caption vertically based on config setting
            if cfg.caption_position == "bottom":
                start_y = 1920 - total_height - 200
            elif cfg.caption_position == "top":
                start_y = 200
            else:
                start_y = (1920 - total_height) // 2

            # Render individual clips for each word's active speak time
            for w in words:
                w_start = w["start"]
                w_end = w["end"]
                w_dur = w_end - w_start
                if w_dur <= 0:
                    w_dur = 0.15

                # Generate transparent subtitle card image
                pil_img = self._render_caption_image(
                    lines=lines,
                    active_word_obj=w,
                    font=font,
                    start_y=start_y,
                    line_spacing=line_spacing,
                    space_w=space_w,
                    bg_box=bool(cfg.caption_bg_color)
                )

                # Convert to numpy array and create an ImageClip
                img_arr = np.array(pil_img)
                rgb_arr = img_arr[:, :, :3]
                alpha_arr = img_arr[:, :, 3] / 255.0

                txt_clip = ImageClip(rgb_arr)
                try:
                    mask_clip = ImageClip(alpha_arr, ismask=True)
                except TypeError:
                    mask_clip = ImageClip(alpha_arr)
                
                if hasattr(txt_clip, "with_mask"):
                    txt_clip = txt_clip.with_mask(mask_clip)
                else:
                    txt_clip = txt_clip.set_mask(mask_clip)

                txt_clip = safe_with_start(txt_clip, w_start)
                txt_clip = safe_with_duration(txt_clip, w_dur)
                txt_clip = safe_with_position(txt_clip, ("center", "center"))
                
                caption_clips.append(txt_clip)

        # Mix Narration and Background Music
        final_audio_track = narration
        if cfg.music_path and os.path.exists(cfg.music_path):
            try:
                music = AudioFileClip(cfg.music_path)
                music = safe_volume(music, cfg.music_volume)
                
                if music.duration < cfg.duration:
                    if hasattr(music, "loop"):
                        music = music.loop(duration=cfg.duration)
                    else:
                        from moviepy.audio.fx.loop import loop as aloop
                        music = aloop(music, duration=cfg.duration)
                else:
                    music = safe_subclip(music, 0, cfg.duration)

                final_audio_track = CompositeAudioClip([
                    safe_volume(narration, 1.0),
                    music
                ])
                logger.info(f"Successfully mixed background music: {cfg.music_path}")
            except Exception as e:
                logger.warning(f"Failed to mix background music: {e}")

        # Bind audio mix to the background video clip
        background = safe_with_audio(background, final_audio_track)

        # Layer captions on top of the background video
        all_clips = [background] + caption_clips
        final_video = CompositeVideoClip(all_clips, size=(1080, 1920))
        final_video = safe_with_duration(final_video, cfg.duration)

        os.makedirs(os.path.dirname(cfg.output_path), exist_ok=True)
        final_video.write_videofile(
            cfg.output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            preset="medium",
            threads=2,
            logger=None,
        )

        # Resource clean-up
        final_video.close()
        background.close()
        narration.close()
        for c in caption_clips:
            if hasattr(c, 'close'):
                c.close()

        logger.info(f"Short video rendered successfully: {cfg.output_path}")
        return cfg.output_path

