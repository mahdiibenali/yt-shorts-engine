import os
import asyncio
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self):
        self.voice = settings.tts_voice

    async def generate(self, text: str, output_path: str, voice: Optional[str] = None) -> str:
        import edge_tts
        selected_voice = voice or self.voice
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_path)
        logger.info(f"TTS saved to {output_path} (voice: {selected_voice})")
        return output_path

    async def get_available_voices(self) -> list:
        import edge_tts
        voices = await edge_tts.list_voices()
        return [
            {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
            for v in voices
        ]

    @staticmethod
    def get_duration(audio_path: str) -> float:
        from moviepy import AudioFileClip
        with AudioFileClip(audio_path) as clip:
            return clip.duration
