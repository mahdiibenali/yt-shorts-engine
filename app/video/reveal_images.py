"""Real-animal reveal photos for WhoDatCritter, sourced from Wikimedia Commons.

Every episode's payoff shot is a genuine wildlife photograph instead of an
AI-generated hero image.  Commons is keyless and CC/PD licensed; we bias the
search toward curated high-quality files and record the license for attribution.
"""

import json
import logging
import os
import re

import requests
from PIL import Image

logger = logging.getLogger(__name__)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "WhoDatCritter/1.0 (educational kid shorts; keyless)"
)

# Search tiers from most trusted to least.  The quoted name keeps relevance
# high; incategory pins curated galleries first.
SEARCH_TIERS = [
    'filetype:bitmap "{name}" incategory:"Quality images"',
    'filetype:bitmap "{name}" incategory:"Featured pictures on Wikimedia Commons"',
    'filetype:bitmap "{name}" incategory:"Value images"',
    'filetype:bitmap "{name}"',
]

MIN_WIDTH = 1080
MIN_HEIGHT = 700
ALLOWED_EXTS = (".jpg", ".jpeg", ".png")

# Red flags that a Commons hit is a map/diagram/illustration rather than a
# photograph of the live animal.  The search engine already biases toward the
# species via the quoted common name, so we only *exclude* obvious non-photos
# instead of requiring the filename to contain the name (titles vary by language).
REJECT_WORDS = (
    "map", "diagram", "chart", "distribution", "illustration", "drawing",
    "sketch", "skeleton", "skull", "taxidermy", "museum specimen", "painting",
    "logo", "icon", "svg", "range", "habitat map",
    # non-animal subjects that can share a species' name (e.g. the research
    # vessel "Seahorse II", seahorse sculptures, street-food skewers, ...)
    "ship", "boat", "vessel", "yacht", "ferry", "submarine", "research vessel",
    "sculpture", "statue", "monument", "skewer", "mummified", "decoration",
    "turret", "diesel", "engine",
)


def _query(params: dict) -> dict:
    """Small wrapper around the Commons API (GET, JSON, keyless)."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        **params,
    }
    resp = requests.get(
        COMMONS_API,
        params=params,
        timeout=30.0,
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    return resp.json()


def _norm(text: str) -> str:
    return (text or "").lower().strip()


def _title_matches(title: str, keywords: list[str]) -> bool:
    t = _norm(title)
    return any(_norm(k) in t for k in keywords)


def _is_photo(filename: str, width: int, height: int) -> bool:
    if not filename.lower().endswith(ALLOWED_EXTS):
        return False
    if not width or not height:
        return False
    return width >= MIN_WIDTH and height >= MIN_HEIGHT


def _extract_meta(imageinfo: dict) -> dict:
    meta = {"license": None, "artist": None, "page": None, "description": None}
    try:
        ext = imageinfo.get("extmetadata") or {}
        lic = ext.get("LicenseShortName", {}).get("value")
        if not lic:
            lic = ext.get("LicenseName", {}).get("value")
        meta["license"] = lic
        artist = ext.get("Artist", {}).get("value")
        if artist:
            meta["artist"] = re.sub(r"<[^>]+>", "", artist).strip()
        desc = ext.get("ImageDescription", {}).get("value")
        if desc:
            meta["description"] = re.sub(r"<[^>]+>", "", desc).strip()
        meta["page"] = imageinfo.get("descriptionurl")
    except Exception as e:
        logger.warning("Could not parse license metadata: %s", e)
    return meta


def search_candidates(search_name: str, limit: int = 10) -> list[dict]:
    """Run the trusted-source search tiers and return candidate hits."""
    for tier in SEARCH_TIERS:
        q = tier.format(name=search_name.strip('"'))
        data = _query(
            {
                "generator": "search",
                "gsrsearch": q,
                "gsrnamespace": "6",
                "gsrlimit": str(limit),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": "1080",
            }
        )
        pages = (data.get("query") or {}).get("pages") or []
        if pages:
            logger.info("Commons tier matched %d candidates: %s", len(pages), tier)
            return pages
    return []


def pick_best(hits: list[dict], keywords: list[str]) -> tuple | None:
    """Pick the best real-animal photo from search hits.

    Keeps photo files large enough to fill the split-screen top half, rejects
    obvious non-photos (maps/diagrams/etc.), and prefers hits whose filename or
    description actually names the animal.  Returns ``(hit, info, meta)``.
    """
    scored = []
    for hit in hits:
        info = (hit.get("imageinfo") or [None])[0]
        if not info:
            continue
        title = hit.get("title", "")
        w = info.get("width") or 0
        h = info.get("height") or 0
        if not _is_photo(title, w, h):
            continue
        meta = _extract_meta(info)
        combined = _norm(title) + " " + _norm(meta.get("description"))
        if any(w in combined for w in REJECT_WORDS):
            continue
        boost = 2_000_000 if (
            _title_matches(title, keywords)
            or any(_norm(k) in _norm(meta.get("description")) for k in keywords)
        ) else 0
        scored.append((w * h + boost, hit, info, meta))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0]


def download_photo(url: str, dest_path: str) -> None:
    """Download a photo to *dest_path* (cached — skip if it already exists)."""
    if os.path.exists(dest_path):
        return
    resp = requests.get(
        url,
        timeout=90.0,
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(resp.content)


def resolve_and_download(
    search_name: str,
    keywords: list[str],
    data_dir: str,
    override_url: str | None = None,
    width: int = 1080,
) -> tuple[str | None, dict]:
    """Resolve a trusted real photo for *search_name* and cache it locally.

    Returns ``(local_path_or_None, meta)`` where *meta* carries source/license
    info for attribution.  ``None`` path means no usable photo was found.
    """
    meta_path = os.path.join(data_dir, "reveal_meta.json")
    reveal_path = os.path.join(data_dir, "reveal.jpg")
    os.makedirs(data_dir, exist_ok=True)

    if os.path.exists(reveal_path) and os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return reveal_path, json.load(f)
        except Exception:
            pass

    url = override_url
    meta: dict = {"source": "override", "license": None, "artist": None, "page": None}
    if url is None:
        hits = search_candidates(search_name)
        best = pick_best(hits, keywords)
        if best is None:
            logger.warning("No trusted Commons photo found for %r", search_name)
            return None, meta
        _score, _hit, info, _meta = best
        url = info.get("thumburl") or info.get("url")
        meta = {"source": "commons", **_extract_meta(info)}

    try:
        download_photo(url, reveal_path)
        img = Image.open(reveal_path)
        img.verify()
        img = Image.open(reveal_path)
        if img.size[0] < 200 or img.size[1] < 200:
            logger.warning("Reveal image suspiciously small: %s", img.size)
            return None, meta
        meta["page"] = meta.get("page")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info("Reveal photo ready: %s (%s)", reveal_path, meta.get("license"))
        return reveal_path, meta
    except Exception as e:
        logger.warning("Reveal photo download failed: %s", e)
        return None, meta
