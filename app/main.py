import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api.routes import router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

data_dir = settings.data_dir
os.makedirs(os.path.join(data_dir, "videos"), exist_ok=True)
os.makedirs(os.path.join(data_dir, "audio"), exist_ok=True)
os.makedirs(os.path.join(data_dir, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(data_dir, "downloads"), exist_ok=True)
os.makedirs(os.path.join(data_dir, "db"), exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=data_dir), name="static")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info(f"{settings.app_name} v{settings.version} started on port {settings.port}")


def start():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    start()
