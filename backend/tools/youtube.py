"""
YouTube Data API v3 — resumable upload with full metadata.
Requires OAuth token from auth.py (server-side only).
"""

import logging
import os
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from backend.auth import get_credentials, is_youtube_authenticated

logger = logging.getLogger(__name__)

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB — use resumable above this


def _get_youtube_service():
    """Build authenticated YouTube API client."""
    creds = get_credentials()
    if not creds:
        raise RuntimeError("YouTube not authenticated. Visit /auth/login first.")
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy: str = "public",
    category_id: str = "22",
) -> dict[str, Any]:
    """
    Upload MP4 to YouTube with metadata.
    Uses resumable upload for files over 5MB.
    """
    if not is_youtube_authenticated():
        return {
            "status": "error",
            "message": "YouTube not connected. Open /auth/login in browser.",
        }

    path = Path(video_path)
    if not path.is_file():
        return {"status": "error", "message": f"Video file not found: {video_path}"}

    title = (title or "Untitled")[:100]
    description = description or ""
    tags = tags or []

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        youtube = _get_youtube_service()
        media = MediaFileUpload(
            str(path),
            mimetype="video/mp4",
            resumable=path.stat().st_size > CHUNK_SIZE,
            chunksize=CHUNK_SIZE,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("Upload progress: %d%%", int(status.progress() * 100))

        video_id = response.get("id")
        url = f"https://www.youtube.com/watch?v={video_id}"

        return {
            "status": "ok",
            "video_id": video_id,
            "url": url,
            "title": title,
        }
    except Exception as e:
        logger.error("YouTube upload failed: %s", e)
        return {"status": "error", "message": str(e)}


def get_channel_status() -> dict[str, Any]:
    """Return basic channel info if authenticated."""
    if not is_youtube_authenticated():
        return {"connected": False}
    try:
        youtube = _get_youtube_service()
        resp = youtube.channels().list(part="snippet", mine=True).execute()
        items = resp.get("items", [])
        if items:
            ch = items[0]["snippet"]
            return {
                "connected": True,
                "title": ch.get("title"),
                "thumbnail": ch.get("thumbnails", {}).get("default", {}).get("url"),
            }
        return {"connected": True}
    except Exception as e:
        logger.error("Channel status failed: %s", e)
        return {"connected": False, "error": str(e)}


def youtube_tool_description() -> str:
    return (
        "Upload a video to YouTube. Input: JSON with video_path, title, "
        "description, tags (list). Returns video URL."
    )
