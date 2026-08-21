"""
AI Video Generation — Free AI-generated background videos

Supports:
  - Jimeng/Dreamina (ByteDance) via jimeng-api proxy
  - Pollinations.ai free video generation
"""
import os
import logging
import time
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AIVideoResult:
    """Result from AI video generation."""
    url: str
    provider: str
    duration: float
    width: int
    height: int


class JimengVideoClient:
    """
    Generate AI video using Jimeng (即梦) / Dreamina.

    Requires jimeng-api to be running (Docker container).
    See: https://github.com/mageia/jimeng-api

    Supports:
      - Text-to-video generation
      - 9:16 portrait ratio (perfect for Shorts)
      - Multiple models: jimeng-video-3.5-pro, jimeng-video-3.0, etc.
      - Up to 10s video duration for free
    """

    def __init__(self, base_url: str = "http://localhost:5100", session_id: Optional[str] = None):
        self.base_url = base_url
        self.session_id = session_id  # Jimeng session cookie

    def is_available(self) -> bool:
        """Check if jimeng-api is running."""
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/ping", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_video(self, prompt: str, duration: int = 5, ratio: str = "9:16",
                       model: str = "jimeng-video-3.5-pro") -> Optional[AIVideoResult]:
        """
        Generate a video from text prompt.

        Args:
            prompt: Text description for the video
            duration: Video duration in seconds (5 or 10)
            ratio: Aspect ratio ("9:16" for Shorts)
            model: Jimeng model to use

        Returns:
            AIVideoResult with video URL, or None on failure
        """
        try:
            import httpx

            headers = {"Content-Type": "application/json"}
            if self.session_id:
                headers["Authorization"] = f"Bearer {self.session_id}"

            payload = {
                "model": model,
                "prompt": prompt,
                "ratio": ratio,
                "duration": duration,
            }

            # Jimeng video generation is async — returns a task, we poll for result
            resp = httpx.post(
                f"{self.base_url}/v1/videos/generations",
                json=payload,
                headers=headers,
                timeout=300.0,  # Video gen can take up to 5 minutes
            )

            if resp.status_code != 200:
                logger.warning(f"Jimeng video generation failed: {resp.status_code} {resp.text[:200]}")
                return None

            data = resp.json()

            # Extract video URL from response
            video_data = data.get("data", [{}])
            if not video_data:
                logger.warning("Jimeng returned no video data")
                return None

            video_url = video_data[0].get("url", "")
            if not video_url:
                logger.warning("Jimeng returned empty video URL")
                return None

            # Determine dimensions from ratio
            width, height = 1080, 1920  # Default 9:16
            if ratio == "16:9":
                width, height = 1920, 1080
            elif ratio == "1:1":
                width, height = 1080, 1080

            logger.info(f"Jimeng generated video: {model}, {duration}s, {ratio}")
            return AIVideoResult(
                url=video_url,
                provider="jimeng",
                duration=float(duration),
                width=width,
                height=height,
            )

        except Exception as e:
            logger.warning(f"Jimeng video generation error: {e}")
            return None

    def download_video(self, result: AIVideoResult, output_path: str) -> Optional[str]:
        """Download the generated video to disk."""
        try:
            import httpx
            resp = httpx.get(result.url, follow_redirects=True, timeout=120.0)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded Jimeng video to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Jimeng video download failed: {e}")
        return None


class PollinationsVideoClient:
    """
    Generate AI video using Pollinations.ai.

    NOTE: As of 2026-07, all Pollinations video models (veo, wan, seedance)
    require a paid API key. The POST to /v1/videos/generations will fail
    without one. For free usage, the main pipeline uses the flux image
    model via background.py's PollinationsVideoClient instead.

    See: https://pollinations.ai

    Limitations:
      - Requires paid Pollinations API key for video generation
      - Short clips only (a few seconds)
      - Quality varies
    """

    BASE_URL = "https://gen.pollinations.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key  # Optional, for higher limits

    def is_available(self) -> bool:
        """Pollinations is always available (free, no key required)."""
        return True

    def generate_video(self, prompt: str, model: str = "default") -> Optional[AIVideoResult]:
        """
        Generate a short video from text prompt.

        Args:
            prompt: Description for the video
            model: Video model to use

        Returns:
            AIVideoResult or None on failure
        """
        try:
            import httpx

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": model,
                "prompt": f"{prompt}, vertical 9:16 aspect ratio, cinematic, smooth motion",
            }

            resp = httpx.post(
                f"{self.BASE_URL}/v1/videos/generations",
                json=payload,
                headers=headers,
                timeout=180.0,  # AI generation takes time
            )

            if resp.status_code != 200:
                logger.warning(f"Pollinations video failed: {resp.status_code}")
                return None

            data = resp.json()
            video_data = data.get("data", [{}])
            if not video_data:
                return None

            video_url = video_data[0].get("url", "")
            if not video_url:
                return None

            logger.info(f"Pollinations generated video for: {prompt[:50]}")
            return AIVideoResult(
                url=video_url,
                provider="pollinations",
                duration=5.0,
                width=1080,
                height=1920,
            )

        except Exception as e:
            logger.warning(f"Pollinations video error: {e}")
            return None

    def download_video(self, result: AIVideoResult, output_path: str) -> Optional[str]:
        """Download the generated video to disk."""
        try:
            import httpx
            resp = httpx.get(result.url, follow_redirects=True, timeout=120.0)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded Pollinations video to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Pollinations video download failed: {e}")
        return None


class AIVideoRouter:
    """
    Tries AI video generation providers in priority order.

    Order: Jimeng → Pollinations
    """

    def __init__(self, jimeng_url: str = "http://localhost:5100",
                 jimeng_session: Optional[str] = None,
                 pollinations_key: Optional[str] = None):
        self.providers = []
        self.providers.append(JimengVideoClient(base_url=jimeng_url, session_id=jimeng_session))
        self.providers.append(PollinationsVideoClient(api_key=pollinations_key))

    def generate_and_download(self, prompt: str, output_path: str,
                               duration: int = 5, ratio: str = "9:16") -> Optional[str]:
        """
        Try each AI video provider in order.

        Returns the output path on success, None on failure.
        """
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"AI video provider {provider.__class__.__name__} not available")
                continue

            logger.info(f"Trying AI video: {provider.__class__.__name__}")

            if isinstance(provider, JimengVideoClient):
                result = provider.generate_video(prompt, duration=duration, ratio=ratio)
            else:
                result = provider.generate_video(prompt)

            if result:
                path = provider.download_video(result, output_path)
                if path:
                    return path

        logger.warning("All AI video providers failed")
        return None
