"""
TikTok Content Posting API — direct video post when access token is configured.
Docs: https://developers.tiktok.com/doc/content-posting-api-get-started
"""

import logging
from pathlib import Path
from typing import Any

import requests

from backend.config import (
    TIKTOK_ACCESS_TOKEN,
    TIKTOK_CLIENT_KEY,
    TIKTOK_CLIENT_SECRET,
    tiktok_configured,
)

logger = logging.getLogger(__name__)

TIKTOK_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
TIKTOK_PUBLISH_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def get_tiktok_status() -> dict[str, Any]:
    """Check if TikTok credentials are configured."""
    return {
        "connected": tiktok_configured(),
        "has_client": bool(TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET),
    }


def post_to_tiktok(
    video_path: str,
    caption: str,
    privacy_level: str = "PUBLIC_TO_EVERYONE",
) -> dict[str, Any]:
    """
    Post video to TikTok via Content Posting API (inbox upload flow).
    Requires TIKTOK_ACCESS_TOKEN with video.publish scope.
    """
    if not tiktok_configured():
        return {
            "status": "error",
            "message": "TikTok not configured. Set TIKTOK_CLIENT_KEY, SECRET, and ACCESS_TOKEN in .env",
        }

    path = Path(video_path)
    if not path.is_file():
        return {"status": "error", "message": f"Video not found: {video_path}"}

    try:
        file_size = path.stat().st_size
        headers = {
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        # Step 1: Initialize upload
        init_body = {
            "post_info": {
                "title": caption[:150],
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": min(file_size, 10 * 1024 * 1024),
                "total_chunk_count": 1,
            },
        }

        init_resp = requests.post(
            TIKTOK_INIT_URL,
            headers=headers,
            json=init_body,
            timeout=30,
        )
        init_data = init_resp.json()

        if init_resp.status_code != 200:
            error = init_data.get("error", init_data)
            return {
                "status": "error",
                "message": f"TikTok init failed: {error}",
            }

        upload_url = init_data.get("data", {}).get("upload_url")
        publish_id = init_data.get("data", {}).get("publish_id")

        if not upload_url:
            return {"status": "error", "message": "No upload_url from TikTok"}

        # Step 2: Upload video bytes
        with open(path, "rb") as f:
            video_data = f.read()

        upload_resp = requests.put(
            upload_url,
            data=video_data,
            headers={"Content-Type": "video/mp4"},
            timeout=300,
        )

        if upload_resp.status_code not in (200, 201):
            return {
                "status": "error",
                "message": f"TikTok upload failed: HTTP {upload_resp.status_code}",
            }

        return {
            "status": "ok",
            "platform": "tiktok",
            "publish_id": publish_id,
            "message": "Video uploaded to TikTok. Processing may take a few minutes.",
            "caption": caption[:150],
        }
    except Exception as e:
        logger.error("TikTok post failed: %s", e)
        return {"status": "error", "message": str(e)}


def tiktok_tool_description() -> str:
    return (
        "Post video to TikTok. Input: JSON with video_path and caption. "
        "Requires TikTok API token in environment."
    )
