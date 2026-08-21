import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import declarative_base, sessionmaker
import enum

from app.config import settings

db_dir = os.path.join(settings.data_dir, "db")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "shorts_engine.db")
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ScriptStatus(str, enum.Enum):
    RAW = "raw"
    EDITING = "editing"
    APPROVED = "approved"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADED = "uploaded"


class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    source_url = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    comments = Column(Text, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    status = Column(SAEnum(ScriptStatus), default=ScriptStatus.RAW)
    tags = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, nullable=True)
    youtube_video_id = Column(String, nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(String, primary_key=True)
    script_id = Column(String, nullable=False)
    youtube_video_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    quota_cost = Column(Integer, default=1658)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
