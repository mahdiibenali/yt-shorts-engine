"""
AI Script Writer — Generates and refines YouTube Shorts scripts.

Uses the SmartRouter to automatically pick the best available free AI provider:
  Ollama (local) → g4f (free cloud) → 9Router → OpenAI → Template fallback
"""
import logging
from typing import Optional

from app.config import settings
from app.content.ai_providers import SmartRouter

logger = logging.getLogger(__name__)


class AIWriter:
    def __init__(self):
        self.router = SmartRouter.from_settings(settings)

    def is_available(self) -> bool:
        """Always returns True — the template fallback guarantees generation."""
        return True

    def get_provider_status(self) -> list:
        """Return availability status for all configured AI providers."""
        return self.router.get_status()

    def generate_script(self, theme: str, style: str = "engaging") -> Optional[str]:
        """Generate a viral YouTube Shorts script for a given theme."""
        system_prompt = (
            "You are a viral YouTube Shorts script writer. "
            "You write scripts that are under 60 seconds when read aloud. "
            "Your scripts hook viewers in the first 2 seconds, use short punchy sentences, "
            "and always end with a call to action."
        )

        prompt = (
            f"Write a viral YouTube Shorts script on: '{theme}'.\n"
            f"Rules:\n"
            f"- Start with a strong hook that grabs attention in the first 2 seconds\n"
            f"- Keep it under 60 seconds when read aloud (about 150 words max)\n"
            f"- Engaging, conversational tone\n"
            f"- Short sentences. One idea per line.\n"
            f"- End with a call to action (like & subscribe)\n"
            f"- No markdown, no formatting, just plain spoken text with natural pauses\n"
            f"- Style: {style}"
        )

        result = self.router.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.8,
        )

        logger.info(f"Script generated via [{result.provider}/{result.model}] for theme: {theme}")
        return result.text

    def refine_script(self, raw_text: str) -> Optional[str]:
        """Refine raw Reddit content into a polished YouTube Shorts script."""
        system_prompt = (
            "You are an editor who transforms raw Reddit content into "
            "viral YouTube Shorts scripts. Keep the core story but make it punchy and concise."
        )

        prompt = (
            "Refine this Reddit content into a YouTube Shorts script.\n"
            "Rules:\n"
            "- Keep the core content but make it concise (under 150 words)\n"
            "- Add a hook at the start that stops the scroll\n"
            "- Remove any [deleted], links, usernames, or formatting artifacts\n"
            "- Short sentences. One idea per line.\n"
            "- End with a call to action\n"
            "- No markdown, just plain spoken text\n"
            f"---\n{raw_text[:2000]}\n---"
        )

        result = self.router.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.7,
        )

        logger.info(f"Script refined via [{result.provider}/{result.model}]")
        return result.text
