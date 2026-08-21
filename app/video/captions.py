import os
import json
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\S+")


def _normalize_word(w: str) -> str:
    """Lowercase and strip non-alphanumerics for alignment purposes."""
    return re.sub(r"[^a-z0-9]", "", (w or "").lower())


@dataclass
class CaptionSegment:
    text: str
    start: float
    end: float
    words: Optional[List[Dict]] = None


class CaptionGenerator:
    def __init__(self, model_size: str = "base"):
        self.model = None
        self.model_size = model_size

    def _load_model(self):
        if self.model is None:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def generate(self, audio_path: str) -> List[CaptionSegment]:
        self._load_model()
        try:
            # Request word timestamps from Whisper
            segments, _ = self.model.transcribe(audio_path, language="en", word_timestamps=True)
            
            all_words = []
            for s in segments:
                if s.words:
                    for w in s.words:
                        all_words.append({
                            "word": w.word.strip(),
                            "start": w.start,
                            "end": w.end,
                        })

            if not all_words:
                logger.warning("No word-level timestamps returned, falling back to segment level")
                # Fallback to standard transcription segments
                segments, _ = self.model.transcribe(audio_path, language="en")
                return [
                    CaptionSegment(text=s.text.strip(), start=s.start, end=s.end, words=[])
                    for s in segments
                ]

            # Group words into punchy phrase segments (ideal for shorts: 3-4 words max)
            grouped_segments = []
            current_words = []

            for i, w in enumerate(all_words):
                current_words.append(w)
                
                # Check for split conditions:
                # - 4 words maximum in a subtitle card
                # - Punctuation ending a clause
                # - Large gap/pause before the next word
                ends_with_clause = w["word"] and w["word"][-1] in (".", "?", "!", ",", ";")
                large_gap = False
                if i < len(all_words) - 1:
                    next_word = all_words[i + 1]
                    large_gap = (next_word["start"] - w["end"]) > 0.4

                should_split = len(current_words) >= 4 or ends_with_clause or large_gap

                if should_split:
                    phrase_text = " ".join([cw["word"] for cw in current_words])
                    grouped_segments.append(CaptionSegment(
                        text=phrase_text,
                        start=current_words[0]["start"],
                        end=current_words[-1]["end"],
                        words=current_words,
                    ))
                    current_words = []

            if current_words:
                phrase_text = " ".join([cw["word"] for cw in current_words])
                grouped_segments.append(CaptionSegment(
                    text=phrase_text,
                    start=current_words[0]["start"],
                    end=current_words[-1]["end"],
                    words=current_words,
                ))

            logger.info(f"Generated {len(grouped_segments)} word-level phrase segments from {audio_path}")
            return grouped_segments

        except Exception as e:
            logger.error(f"Error during transcription: {e}. Falling back to empty segments.")
            return []

    def correct_spellings(self, segments: List[CaptionSegment], script_text: str) -> List[CaptionSegment]:
        """Replace Whisper's (possibly mis-spelled) words with the exact
        narration-script words, keeping Whisper timings.

        Because the audio is generated from ``script_text`` via TTS, we know
        exactly what was said.  Words are aligned with the Whisper word tokens
        using difflib; wherever the script and Whisper agree on the word count,
        the correct script spelling wins (e.g. ``slope`` → ``SLOTH!``).
        """
        script_words = _WORD_RE.findall(script_text or "")
        if not script_words:
            return segments

        ws: List[Dict] = []
        for seg in segments:
            seg_words = seg.words or [{"word": seg.text, "start": seg.start, "end": seg.end}]
            seg.words = seg_words
            ws.extend(seg_words)
        if not ws:
            return segments

        import difflib
        sm = difflib.SequenceMatcher(
            a=[_normalize_word(x) for x in script_words],
            b=[_normalize_word(w.get("word", "")) for w in ws],
            autojunk=False,
        )
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    ws[j1 + k]["word"] = script_words[i1 + k]
            elif tag == "replace":
                n = min(i2 - i1, j2 - j1)
                for k in range(n):
                    ws[j1 + k]["word"] = script_words[i1 + k]

        for seg in segments:
            seg.text = " ".join(w["word"] for w in seg.words)
        return segments

    def format_srt(self, segments: List[CaptionSegment]) -> str:
        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines = []
        for i, seg in enumerate(segments, 1):
            lines.append(str(i))
            lines.append(f"{fmt_time(seg.start)} --> {fmt_time(seg.end)}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    def format_word_timings(self, segments: List[CaptionSegment], audio_path: str) -> List[Dict]:
        self._load_model()
        segs, _ = self.model.transcribe(audio_path, language="en", word_timestamps=True)
        word_timings = []
        for seg in segs:
            if seg.words:
                for word in seg.words:
                    word_timings.append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                    })
        return word_timings

