import os
import pickle
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
DAILY_QUOTA = 10000
VIDEO_QUOTA_COST = 1658


class YouTubeUploader:
    def __init__(self):
        self.service = None
        self.token_path = os.path.join(settings.data_dir, "youtube_token.pickle")

    def _authenticate(self):
        credentials = None

        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as f:
                credentials = pickle.load(f)

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open(self.token_path, "wb") as f:
                pickle.dump(credentials, f)

        if not credentials or not credentials.valid:
            client_secrets = settings.youtube_client_secrets_file
            if not os.path.exists(client_secrets):
                raise FileNotFoundError(
                    f"YouTube client secrets not found at {client_secrets}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
            credentials = flow.run_local_server(port=0)
            with open(self.token_path, "wb") as f:
                pickle.dump(credentials, f)

        self.service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        logger.info("YouTube authenticated")

    def _check_quota(self) -> int:
        """Returns number of videos uploaded today"""
        if not self.service:
            self._authenticate()

        request = self.service.videos().list(
            part="snippet,statistics",
            mine=True,
            maxResults=50,
        )
        response = request.execute()

        today = datetime.now(timezone.utc).date()
        count = 0
        for item in response.get("items", []):
            published = item["snippet"]["publishedAt"]
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00")).date()
            if pub_date == today:
                count += 1

        logger.info(f"Videos uploaded today: {count}")
        return count

    def upload(self, video_path: str, title: str, description: str, tags: list,
               thumbnail_path: Optional[str] = None,
               privacy_status: str = "public",
               scheduled_time: Optional[datetime] = None) -> Optional[str]:
        if not self.service:
            self._authenticate()

        uploaded_today = self._check_quota()
        if uploaded_today >= 6:
            logger.warning("Daily upload limit reached (6 videos)")
            return None

        quota_used = uploaded_today * VIDEO_QUOTA_COST + VIDEO_QUOTA_COST
        if quota_used > DAILY_QUOTA:
            logger.warning(f"Daily quota would be exceeded: {quota_used} > {DAILY_QUOTA}")
            return None

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        try:
            response = request.execute()
            video_id = response.get("id")
            logger.info(f"Uploaded video: {title} -> https://youtu.be/{video_id}")

            if thumbnail_path and os.path.exists(thumbnail_path):
                self.service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path),
                ).execute()
                logger.info(f"Thumbnail set for {video_id}")

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

        return response.get("id")

    def get_channel_stats(self) -> Optional[dict]:
        if not self.service:
            self._authenticate()

        channels = self.service.channels().list(part="statistics", mine=True).execute()
        if channels.get("items"):
            return channels["items"][0]["statistics"]
        return None
