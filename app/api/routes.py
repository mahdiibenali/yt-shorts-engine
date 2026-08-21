import os
import uuid
import json
import asyncio
import logging
from datetime import datetime, timezone
import random
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.database import SessionLocal, Script, ScriptStatus, UploadLog
from app.content.reddit import RedditScraper
from app.content.ai_writer import AIWriter
from app.audio.tts import TTSEngine
from app.video.background import PexelsClient, VideoSourceRouter
from app.video.captions import CaptionGenerator
from app.render.composer import VideoComposer, CompositionConfig, CaptionSegment
from app.render.thumbnail import ThumbnailGenerator
from app.upload.youtube import YouTubeUploader
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

reddit = RedditScraper()
ai_writer = AIWriter()
tts = TTSEngine()
pexels = PexelsClient()  # Legacy, kept for backward compatibility
video_sources = VideoSourceRouter.from_settings()
captions = CaptionGenerator()
composer = VideoComposer()
thumbnail_gen = ThumbnailGenerator()
uploader = YouTubeUploader()


class ScriptCreate(BaseModel):
    source: str = "manual"
    title: str
    content: str
    source_url: Optional[str] = None
    tags: Optional[str] = None


class ScriptReview(BaseModel):
    script_id: str
    approved: bool
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None


class RedditFetchRequest(BaseModel):
    subreddit: str = "AskReddit"
    limit: int = 5
    min_comments: int = 300


class AIScriptRequest(BaseModel):
    theme: str
    style: str = "engaging"


class GenerateRequest(BaseModel):
    script_id: str
    voice: Optional[str] = None
    caption_position: str = "bottom"
    add_music: bool = True
    gameplay_video_path: Optional[str] = None


# --- Content Endpoints ---

@router.post("/content/reddit")
def fetch_reddit(req: RedditFetchRequest):
    if not reddit.is_available():
        raise HTTPException(400, "Reddit not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
    posts = reddit.fetch_posts(subreddit=req.subreddit, limit=req.limit, min_comments=req.min_comments)
    results = []
    db = SessionLocal()
    try:
        for post in posts:
            script = reddit.format_script_for_review(post)
            existing = db.query(Script).filter(Script.source_url == script["source_url"]).first()
            if existing:
                continue
            db_script = Script(
                id=str(uuid.uuid4()),
                source=script["source"],
                source_url=script["source_url"],
                title=script["title"],
                content=script["content"],
                status=ScriptStatus.RAW,
            )
            db.add(db_script)
            db.commit()
            script["id"] = db_script.id
            results.append(script)
    finally:
        db.close()
    return {"scripts": results}


@router.post("/content/ai-script")
def generate_ai_script(req: AIScriptRequest):
    script_text = ai_writer.generate_script(req.theme, req.style)
    if not script_text:
        raise HTTPException(500, "AI script generation failed")
    return {"theme": req.theme, "content": script_text}


@router.get("/ai-providers/status")
def get_ai_provider_status():
    return {"providers": ai_writer.get_provider_status()}


@router.get("/video-sources/status")
def get_video_source_status():
    """Return availability of all background video sources."""
    return {"sources": video_sources.get_status()}



@router.post("/scripts")
def create_script(req: ScriptCreate):
    db = SessionLocal()
    try:
        script = Script(
            id=str(uuid.uuid4()),
            source=req.source,
            source_url=req.source_url,
            title=req.title,
            content=req.content,
            tags=req.tags,
            status=ScriptStatus.RAW,
        )
        db.add(script)
        db.commit()
        return {"id": script.id, "title": script.title, "status": script.status.value}
    finally:
        db.close()


@router.get("/scripts")
def list_scripts(status: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(Script)
        if status:
            query = query.filter(Script.status == ScriptStatus(status))
        scripts = query.order_by(Script.created_at.desc()).limit(50).all()
        return {
            "scripts": [
                {
                    "id": s.id,
                    "title": s.title,
                    "source": s.source,
                    "status": s.status.value,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in scripts
            ]
        }
    finally:
        db.close()


@router.get("/scripts/{script_id}")
def get_script(script_id: str):
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(404, "Script not found")
        return {
            "id": script.id,
            "title": script.title,
            "content": script.content,
            "source": script.source,
            "source_url": script.source_url,
            "status": script.status.value,
            "tags": script.tags,
            "description": script.description,
            "video_path": script.video_path,
            "youtube_video_id": script.youtube_video_id,
            "created_at": script.created_at.isoformat() if script.created_at else None,
        }
    finally:
        db.close()


@router.put("/scripts/{script_id}/review")
def review_script(script_id: str, req: ScriptReview):
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(404, "Script not found")

        if req.approved:
            script.status = ScriptStatus.APPROVED
            if req.title:
                script.title = req.title
            if req.content:
                script.content = req.content
            if req.tags:
                script.tags = req.tags
            if req.description:
                script.description = req.description
        else:
            script.status = ScriptStatus.RAW
            script.content = "[REJECTED] " + script.content

        db.commit()
        return {"id": script.id, "status": script.status.value}
    finally:
        db.close()


# --- Generation Endpoints ---

@router.post("/generate/{script_id}")
async def generate_video(script_id: str, req: GenerateRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(404, "Script not found")
        if script.status != ScriptStatus.APPROVED:
            raise HTTPException(400, f"Script must be APPROVED, current: {script.status.value}")

        script.status = ScriptStatus.GENERATING
        db.commit()
    finally:
        db.close()

    background_tasks.add_task(_generate_video_task, script_id, req.voice, req.caption_position, req.add_music, req.gameplay_video_path)
    return {"message": "Generation started", "script_id": script_id}


async def _generate_video_task(script_id: str, voice: Optional[str], caption_position: str, add_music: bool, gameplay_video_path: Optional[str] = None):
    import os
    db = SessionLocal()
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            return

        safe_title = "".join(c for c in script.title if c.isalnum() or c in " _-")[:30].strip()

        audio_path = os.path.join(settings.data_dir, "audio", f"{script_id}.mp3")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        await tts.generate(script.content, audio_path, voice=voice)

        segs = captions.generate(audio_path)
        duration = tts.get_duration(audio_path) + 1.0

        bg_video_path = os.path.join(settings.data_dir, "downloads", f"{script_id}_bg.mp4")
        os.makedirs(os.path.dirname(bg_video_path), exist_ok=True)

        search_term = safe_title or "nature"
        # Use the multi-source router: Pexels → Pixabay → Coverr → Pollinations AI
        bg_result = video_sources.search_and_download(
            query=search_term,
            output_path=bg_video_path,
            min_duration=duration,
        )
        if not bg_result:
            logger.warning("No background video found from any source, using color clip")
            bg_video_path = None

        music_path = None
        if add_music:
            music_dir = os.path.join(settings.data_dir, "..", "app", "assets", "music")
            if os.path.exists(music_dir):
                tracks = [f for f in os.listdir(music_dir) if f.endswith((".mp3", ".wav"))]
                if tracks:
                    music_path = os.path.join(music_dir, random.choice(tracks))

        if bg_video_path and not os.path.exists(bg_video_path):
            bg_video_path = None

        os.makedirs(os.path.join(settings.data_dir, "videos"), exist_ok=True)
        output_path = os.path.join(settings.data_dir, "videos", f"{script_id}.mp4")

        cfg = CompositionConfig(
            background_video_path=bg_video_path,
            audio_path=audio_path,
            captions=segs,
            output_path=output_path,
            duration=duration,
            caption_position=caption_position,
            music_path=music_path,
            gameplay_video_path=gameplay_video_path,
        )
        composer.compose(cfg)

        thumbnail_path = os.path.join(settings.data_dir, "thumbnails", f"{script_id}.jpg")
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        thumbnail_gen.generate(script.title, thumbnail_path)

        script.status = ScriptStatus.COMPLETED
        script.video_path = output_path
        db.commit()

        uploader = YouTubeUploader()
        tags_list = (script.tags or "").split(",") if script.tags else [script.title]
        video_id = uploader.upload(
            video_path=output_path,
            title=script.title,
            description=script.description or f"#shorts {script.title}",
            tags=tags_list,
            thumbnail_path=thumbnail_path,
        )
        if video_id:
            script.youtube_video_id = video_id
            script.status = ScriptStatus.UPLOADED
            script.uploaded_at = datetime.now(timezone.utc)
            db.commit()

    except Exception as e:
        logger.error(f"Generation failed for {script_id}: {e}")
        script = db.query(Script).filter(Script.id == script_id).first()
        if script:
            script.status = ScriptStatus.FAILED
            db.commit()
    finally:
        db.close()


# --- Status & Health ---

@router.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": settings.version}


@router.get("/stats")
def stats():
    db = SessionLocal()
    try:
        total = db.query(Script).count()
        uploaded = db.query(Script).filter(Script.status == ScriptStatus.UPLOADED).count()
        failed = db.query(Script).filter(Script.status == ScriptStatus.FAILED).count()
        pending = db.query(Script).filter(Script.status == ScriptStatus.APPROVED).count()
        return {
            "total_scripts": total,
            "uploaded": uploaded,
            "failed": failed,
            "pending_generation": pending,
        }
    finally:
        db.close()


@router.get("/voices")
async def list_voices():
    voices = await tts.get_available_voices()
    return {"voices": voices}


