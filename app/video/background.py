"""
Background Video Source Router — Finds and downloads stock/AI-generated background videos.

Uses a provider chain similar to the AI SmartRouter:
  Pexels → Pixabay → Coverr → Pollinations (AI-generated)

Each provider implements the same interface:
  - is_available() → bool
  - search_video(query, min_duration, orientation) → Optional[dict]
  - download_video(video_info, output_path) → Optional[str]
"""

import os
import random
import logging
import urllib.parse
from typing import Optional, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider 1: Pexels (requires API key)
# ---------------------------------------------------------------------------

class PexelsClient:
    BASE_URL = "https://api.pexels.com/videos"

    def __init__(self):
        self.api_key = settings.pexels_api_key
        self.client = httpx.Client(
            headers={"Authorization": self.api_key},
            timeout=30.0,
        ) if self.api_key else None

    def is_available(self) -> bool:
        return self.api_key is not None and self.client is not None

    def search_video(self, query: str, min_duration: float = 5.0, orientation: str = "portrait") -> Optional[dict]:
        if not self.is_available():
            logger.warning("Pexels not configured")
            return None

        fallback_queries = ["nature", "city", "space", "ocean", "abstract", "technology"]
        queries_to_try = [query] + fallback_queries

        for q in queries_to_try:
            try:
                resp = self.client.get(
                    f"{self.BASE_URL}/search",
                    params={"query": q, "per_page": 15, "orientation": orientation, "size": "medium"},
                )
                if resp.status_code != 200:
                    continue

                data = resp.json()
                videos = data.get("videos", [])
                if not videos:
                    continue

                valid = []
                for v in videos:
                    v_duration = v.get("duration", 0)
                    for file in v.get("video_files", []):
                        if (v_duration >= min_duration or v_duration >= 5.0) and file.get("width", 0) >= 480:
                            valid.append({
                                "url": file["link"],
                                "width": file.get("width"),
                                "height": file.get("height"),
                                "duration": v_duration,
                                "query": q,
                            })
                            break  # Just need one valid file quality per video
                if valid:
                    choice = random.choice(valid)
                    logger.info(f"Pexels: found video for '{q}' ({choice['width']}x{choice['height']}, duration: {choice['duration']}s)")
                    return choice
            except Exception as e:
                logger.warning(f"Pexels search failed for '{q}': {e}")

        logger.warning(f"Pexels: no video found for any query")
        return None

    def download_video(self, video_info: dict, output_path: str) -> Optional[str]:
        try:
            resp = httpx.get(video_info["url"], follow_redirects=True, timeout=60.0)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded background video to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Provider 2: Pixabay (requires free API key)
# ---------------------------------------------------------------------------

class PixabayClient:
    """Pixabay free stock video API.

    Get a free API key at https://pixabay.com/api/docs/.
    Set ``PIXABAY_API_KEY`` in your ``.env`` file.
    """

    BASE_URL = "https://pixabay.com/api/videos/"

    def __init__(self):
        self.api_key = getattr(settings, "pixabay_api_key", None)

    @property
    def name(self) -> str:
        return "pixabay"

    def is_available(self) -> bool:
        return self.api_key is not None

    def search_video(self, query: str, min_duration: float = 5.0, orientation: str = "portrait") -> Optional[dict]:
        """Search Pixabay for a stock video matching *query*."""
        if not self.is_available():
            logger.warning("Pixabay not configured (no API key)")
            return None

        # Map orientation to Pixabay's naming
        pixabay_orientation = "vertical" if orientation == "portrait" else "horizontal"

        fallback_queries = ["nature", "city", "space", "ocean", "abstract", "technology"]
        queries_to_try = [query] + fallback_queries

        for q in queries_to_try:
            try:
                resp = httpx.get(
                    self.BASE_URL,
                    params={
                        "key": self.api_key,
                        "q": q,
                        "per_page": 15,
                        "video_type": "film",
                        "orientation": pixabay_orientation,
                    },
                    timeout=30.0,
                )
                if resp.status_code != 200:
                    logger.debug(f"Pixabay: HTTP {resp.status_code} for '{q}'")
                    continue

                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    continue

                valid = []
                for hit in hits:
                    duration = hit.get("duration", 0)
                    if duration < min_duration and duration < 5.0:
                        continue

                    videos = hit.get("videos", {})
                    # Prefer "large" quality, fall back to "medium"
                    for quality in ("large", "medium"):
                        vfile = videos.get(quality, {})
                        url = vfile.get("url")
                        width = vfile.get("width", 0)
                        height = vfile.get("height", 0)
                        if url and width >= 480:
                            valid.append({
                                "url": url,
                                "width": width,
                                "height": height,
                                "duration": duration,
                                "query": q,
                            })
                            break

                if valid:
                    choice = random.choice(valid)
                    logger.info(
                        f"Pixabay: found video for '{q}' "
                        f"({choice['width']}x{choice['height']}, duration: {choice['duration']}s)"
                    )
                    return choice

            except Exception as e:
                logger.warning(f"Pixabay search failed for '{q}': {e}")

        logger.warning("Pixabay: no video found for any query")
        return None

    def download_video(self, video_info: dict, output_path: str) -> Optional[str]:
        """Download a Pixabay video to *output_path*."""
        try:
            resp = httpx.get(video_info["url"], follow_redirects=True, timeout=60.0)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded background video to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Pixabay download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Provider 3: Coverr (requires free API key)
# ---------------------------------------------------------------------------

class CoverrClient:
    """Coverr free stock video API.

    Get an API key at https://coverr.co/api.
    Set ``COVERR_API_KEY`` in your ``.env`` file.
    """

    BASE_URL = "https://api.coverr.co/videos"

    def __init__(self):
        self.api_key = getattr(settings, "coverr_api_key", None)
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        ) if self.api_key else None

    @property
    def name(self) -> str:
        return "coverr"

    def is_available(self) -> bool:
        return self.api_key is not None and self.client is not None

    def search_video(self, query: str, min_duration: float = 5.0, orientation: str = "portrait") -> Optional[dict]:
        """Search Coverr for a stock video matching *query*."""
        if not self.is_available():
            logger.warning("Coverr not configured (no API key)")
            return None

        fallback_queries = ["nature", "city", "space", "ocean", "abstract", "technology"]
        queries_to_try = [query] + fallback_queries

        for q in queries_to_try:
            try:
                resp = self.client.get(
                    self.BASE_URL,
                    params={"query": q, "page_size": 15},
                )
                if resp.status_code != 200:
                    logger.debug(f"Coverr: HTTP {resp.status_code} for '{q}'")
                    continue

                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    continue

                valid = []
                for hit in hits:
                    duration = hit.get("duration", 0)
                    if duration < min_duration and duration < 5.0:
                        continue

                    # Coverr nests download URLs under "urls"
                    urls = hit.get("urls", {})
                    url = urls.get("mp4") or urls.get("download")
                    if not url:
                        continue

                    width = hit.get("width", 0)
                    height = hit.get("height", 0)
                    valid.append({
                        "url": url,
                        "width": width,
                        "height": height,
                        "duration": duration,
                        "query": q,
                    })

                if valid:
                    choice = random.choice(valid)
                    logger.info(
                        f"Coverr: found video for '{q}' "
                        f"({choice['width']}x{choice['height']}, duration: {choice['duration']}s)"
                    )
                    return choice

            except Exception as e:
                logger.warning(f"Coverr search failed for '{q}': {e}")

        logger.warning("Coverr: no video found for any query")
        return None

    def download_video(self, video_info: dict, output_path: str) -> Optional[str]:
        """Download a Coverr video to *output_path*."""
        try:
            resp = httpx.get(video_info["url"], follow_redirects=True, timeout=60.0)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"Downloaded background video to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Coverr download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Provider 4: Pollinations.ai (free AI-generated video, no key required)
# ---------------------------------------------------------------------------

class PollinationsVideoClient:
    """Pollinations.ai free AI-generated background image (converted to static video).

    Since Pollinations video models require paid API keys, this provider
    generates a high-quality AI background IMAGE using the free ``flux``
    model, which MoviePy can use as a static background clip.

    No API key is required.

    Docs: https://pollinations.ai
    """

    IMAGE_URL = "https://image.pollinations.ai/prompt"

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "pollinations-image"

    def is_available(self) -> bool:
        """Always available — no API key needed."""
        return True

    def search_video(self, query: str, min_duration: float = 5.0, orientation: str = "portrait") -> Optional[dict]:
        """Build a Pollinations image URL for the given query.

        This generates a cinematic AI background image (not video).
        The composer will use it as a static background clip.
        """
        prompt = f"{query}, cinematic background, dramatic lighting, smooth gradients, no text, 9:16 vertical"
        encoded_prompt = urllib.parse.quote(prompt, safe="")
        # Request 9:16 portrait dimensions for Shorts
        url = f"{self.IMAGE_URL}/{encoded_prompt}?width=1080&height=1920&model=flux&nologo=true&seed={random.randint(1, 999999)}"

        logger.info(f"Pollinations: prepared AI background image for '{query}'")
        return {
            "url": url,
            "width": 1080,
            "height": 1920,
            "duration": None,  # Static image — composer will handle duration
            "query": query,
            "source": "pollinations-ai-image",
            "is_image": True,
        }

    def download_video(self, video_info: dict, output_path: str) -> Optional[str]:
        """Download the AI-generated background image.

        Saves as .jpg alongside the expected .mp4 path so the composer
        can detect it's a still image and create a static clip.
        """
        try:
            # Change extension to .jpg for the image
            image_path = os.path.splitext(output_path)[0] + ".jpg"
            logger.info("Pollinations: generating AI background image...")
            resp = httpx.get(
                video_info["url"],
                follow_redirects=True,
                timeout=60.0,
            )
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "image" in content_type or len(resp.content) > 1000:
                    with open(image_path, "wb") as f:
                        f.write(resp.content)
                    file_size = os.path.getsize(image_path)
                    logger.info(
                        f"Pollinations: AI background image saved to {image_path} ({file_size / 1024:.0f} KB)"
                    )
                    return image_path
                else:
                    logger.warning(f"Pollinations: unexpected content type: {content_type}")
            else:
                logger.warning(f"Pollinations: HTTP {resp.status_code}")
        except httpx.TimeoutException:
            logger.warning("Pollinations: image generation request timed out")
        except Exception as e:
            logger.error(f"Pollinations image download failed: {e}")
        return None


# ---------------------------------------------------------------------------
# VideoSourceRouter — tries providers in order until one succeeds
# ---------------------------------------------------------------------------

class VideoSourceRouter:
    """Tries video source providers in priority order and returns the first success.

    Default chain: Pexels → Pixabay → Coverr → Pollinations (AI-generated)

    Usage::

        router = VideoSourceRouter.from_settings()
        path = router.search_and_download("space exploration", "/tmp/bg.mp4")
    """

    def __init__(self, providers: Optional[List] = None):
        self.providers = providers or []
        self._initialized = False

    @classmethod
    def from_settings(cls) -> "VideoSourceRouter":
        """Build the provider chain from application settings."""
        providers = []

        # Tier 1: Pexels (popular stock video API)
        providers.append(PexelsClient())

        # Tier 2: Pixabay (free stock video)
        providers.append(PixabayClient())

        # Tier 3: Coverr (free stock video)
        providers.append(CoverrClient())

        # Tier 4: Pollinations AI (always available, no key needed)
        providers.append(PollinationsVideoClient())

        router = cls(providers=providers)
        router._log_providers()
        return router

    def _log_providers(self):
        """Log which providers are configured."""
        names = []
        for p in self.providers:
            label = getattr(p, "name", p.__class__.__name__)
            status = "✓" if p.is_available() else "✗"
            names.append(f"{label}({status})")
        logger.info(f"VideoSourceRouter initialized: {' → '.join(names)}")

    def search_and_download(
        self,
        query: str,
        output_path: str,
        min_duration: float = 5.0,
        orientation: str = "portrait",
    ) -> Optional[str]:
        """Search for a video and download it, trying each provider in order.

        Args:
            query: Search term for the video (e.g. "space exploration").
            output_path: Where to save the downloaded video file.
            min_duration: Minimum acceptable video duration in seconds.
            orientation: Video orientation — "portrait" or "landscape".

        Returns:
            The *output_path* on success, or ``None`` if all providers failed.
        """
        for provider in self.providers:
            provider_name = getattr(provider, "name", provider.__class__.__name__)

            if not provider.is_available():
                logger.debug(f"{provider_name} not available, skipping")
                continue

            logger.info(f"Trying video source: {provider_name}")

            # Search
            video_info = provider.search_video(
                query=query,
                min_duration=min_duration,
                orientation=orientation,
            )
            if not video_info:
                logger.info(f"{provider_name} returned no results, trying next")
                continue

            # Download
            result = provider.download_video(video_info, output_path)
            if result:
                logger.info(f"Background video sourced from {provider_name}")
                return result
            logger.info(f"{provider_name} download failed, trying next")

        logger.error("All video source providers failed")
        return None

    def get_status(self) -> List[dict]:
        """Return availability status for all providers."""
        return [
            {
                "name": getattr(p, "name", p.__class__.__name__),
                "available": p.is_available(),
            }
            for p in self.providers
        ]
