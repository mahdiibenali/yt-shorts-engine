from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "YT Shorts Engine"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "info"
    port: int = 8000

    # Paths
    data_dir: str = "./data"
    temp_dir: str = "./data/temp"

    # Content - Reddit
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "yt-shorts-engine/1.0"

    # Content - AI Providers (all optional, falls back to templates)
    ai_provider: str = "auto"  # auto | ollama | g4f | pollinations | 9router | openai
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1:8b"
    g4f_model: str = "gpt-4o-mini"
    pollinations_model: str = "openai"  # openai | deepseek | mistral | llama | gemma | qwen-coder | gpt-oss
    pollinations_api_key: Optional[str] = None  # Optional, for higher rate limits
    nine_router_url: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Jimeng/Dreamina AI (requires jimeng-api Docker container)
    jimeng_base_url: Optional[str] = None  # e.g. http://localhost:5100/v1
    jimeng_api_key: Optional[str] = None
    jimeng_session_id: Optional[str] = None  # Jimeng session cookie for video gen
    jimeng_model: str = "jimeng"

    # Video sources — stock footage (all free, keys optional)
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None  # Free at https://pixabay.com/api/docs/
    coverr_api_key: Optional[str] = None  # Free at https://coverr.co/api

    # Image generation — Cloudflare Workers AI (FLUX.2 / FLUX.1)
    cloudflare_account_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
    cloudflare_flux_daily_budget: Optional[int] = None  # neurons/day for klein-9b

    # Image generation — Pollinations (new unified API, currently 0-balance)
    pollinations_token: Optional[str] = None
    pollinations_image_model: Optional[str] = None  # e.g. kontext | zimage | flux

    # Gemini (text/vision free tier used for QA; image models are paid-only)
    gemini_api_key: Optional[str] = None

    # Image generation — Alibaba Cloud Model Studio / DashScope
    dashscope_api_key: Optional[str] = None
    dashscope_base_url: Optional[str] = None
    dashscope_model: Optional[str] = None

    # Image generation — local Stable Diffusion (self-hosted, free/unlimited)
    local_sd_ckpt: Optional[str] = None  # path to a single-file checkpoint
    local_sd_steps: Optional[int] = None
    local_sd_size: Optional[int] = None
    local_sd_negative: Optional[str] = None
    image_provider: Optional[str] = None  # ordered provider chain, e.g. local,cloudflare

    # Cloudflare R2 storage (optional)
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_s3_endpoint: Optional[str] = None

    # YouTube
    youtube_client_secrets_file: str = "client_secrets.json"

    # Processing
    concurrency: int = 1
    whisper_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    max_video_duration: int = 58
    caption_position: str = "bottom"

    # Curiosity Intelligence
    curiosity_db_path: str = "./data/curiosity.db"
    belief_auto_approve_after_days: float = 2.0
    prediction_metric: str = "retention"
    competitor_channels: list[str] = [
        # Animal-facts / critter shorts competitors (Phase E intel)
        "UCSz8X-JAmenxLH-uXlgVaCg",  # Odd Animal Specimens
        "UC5Yo88QF-chdugJbAnB2tUw",  # Casual Geographic
        "UCK-GTQ9HY1UOpJx-yqDcA-Q",  # Animal Facts
        "UCG5_BraUMNcluZPZ__oOeKg",  # Natural World Facts
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
