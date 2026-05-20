"""
Content pipeline: research → write → video → upload → social posts.
Uses tool modules directly (stable for FastAPI); Gemini/Groq SDKs used inside writer.py.
"""

import logging
from typing import Any

from backend.auth import is_youtube_authenticated
from backend.history import add_entry
from backend.tools.research import research_trending
from backend.tools.tiktok import post_to_tiktok
from backend.tools.twitter import generate_tweet
from backend.tools.video import cleanup_work_dir, create_faceless_video
from backend.tools.writer import write_content
from backend.tools.youtube import upload_video

logger = logging.getLogger(__name__)


def run_pipeline(
    niche: str,
    mode: str = "faceless",
    topic: str | None = None,
    video_path: str | None = None,
    post_youtube: bool = True,
    post_tiktok_flag: bool = False,
) -> dict[str, Any]:
    """
    Deterministic pipeline: research → write → video/upload → platforms.
    """
    steps: list[dict[str, Any]] = []
    result: dict[str, Any] = {"status": "ok", "niche": niche, "mode": mode, "steps": steps}

    try:
        # 1. Research
        research = research_trending(niche, topic)
        steps.append({"step": "research", "result": research})
        if research.get("status") == "error":
            return {**result, "status": "error", "message": research.get("message")}

        summary = research.get("summary", "")

        # 2. Write
        content = write_content(niche, summary, mode, topic)
        steps.append({"step": "write", "result": {k: content.get(k) for k in ("title", "status") if k in content}})
        if content.get("status") == "error":
            return {**result, "status": "error", "message": content.get("message")}

        result["content"] = content
        final_video = video_path

        # 3. Video (faceless only)
        if mode == "faceless":
            video_out = create_faceless_video(
                content.get("script", ""),
                content.get("title", ""),
                content.get("keywords"),
            )
            steps.append({"step": "video", "result": {"status": video_out.get("status")}})
            if video_out.get("status") == "error":
                return {**result, "status": "error", "message": video_out.get("message")}
            final_video = video_out.get("video_path")
            result["video_path"] = final_video
            result["work_dir"] = video_out.get("work_dir")

        elif mode == "upload" and not final_video:
            tweet = generate_tweet(niche, summary, existing_tweet=content.get("tweet"))
            result["tweet"] = tweet
            result["status"] = "ok"
            result["message"] = "Metadata ready. Upload your recorded video via /upload."
            add_entry(
                {
                    "niche": niche,
                    "mode": mode,
                    "title": content.get("title"),
                    "status": "awaiting_upload",
                }
            )
            return result

        # 4. YouTube (skip if not connected — user can connect later)
        if post_youtube and final_video and not is_youtube_authenticated():
            result["youtube"] = {
                "status": "skipped",
                "message": "YouTube not connected. Connect in the app to auto-upload.",
            }
            post_youtube = False

        if post_youtube and final_video:
            yt = upload_video(
                final_video,
                content.get("title", ""),
                content.get("description", ""),
                content.get("tags"),
            )
            steps.append({"step": "youtube", "result": yt})
            result["youtube"] = yt
            if yt.get("status") == "ok" and result.get("work_dir"):
                cleanup_work_dir(result["work_dir"])

        # 5. TikTok (optional)
        if post_tiktok_flag and final_video:
            tt = post_to_tiktok(final_video, content.get("tiktok_caption", content.get("title", "")))
            steps.append({"step": "tiktok", "result": tt})
            result["tiktok"] = tt

        # 6. Twitter (copy/paste)
        tweet = generate_tweet(niche, summary, existing_tweet=content.get("tweet"))
        result["twitter"] = tweet

        add_entry(
            {
                "niche": niche,
                "mode": mode,
                "title": content.get("title"),
                "youtube_url": (result.get("youtube") or {}).get("url"),
                "tweet": tweet.get("tweet"),
                "status": result.get("status"),
            }
        )
        return result

    except Exception as e:
        logger.exception("Pipeline failed")
        return {"status": "error", "message": str(e), "steps": steps}
