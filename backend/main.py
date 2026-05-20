"""
FastAPI server for Social Media AI Agent.
Hosted on Railway; PWA on Vercel calls these endpoints.
"""

import logging
import shutil
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from backend.agent import run_pipeline
from backend.auth import create_auth_url, handle_callback, is_youtube_authenticated, revoke_and_clear
from backend.config import FRONTEND_URL, NICHES, MODES, PORT, TEMP_VIDEOS_DIR, ai_configured
from backend.history import get_history
from backend.tools.tiktok import get_tiktok_status
from backend.tools.youtube import get_channel_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Social Media AI Agent",
    description="Research, create, and post content across YouTube, TikTok, and X",
    version="1.0.0",
)

# CORS for PWA (Vercel + local dev)
_origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "https://*.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PWA may be on any Vercel preview URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models ---


class GenerateRequest(BaseModel):
    niche: Literal["football", "movies", "anime", "crypto"]
    mode: Literal["faceless", "upload"] = "faceless"
    topic: Optional[str] = None
    post_youtube: bool = True
    post_tiktok: bool = False


class GenerateResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[dict] = None


# --- Routes ---


@app.get("/ping")
async def ping():
    """Keep Railway awake + health check."""
    return {"status": "ok", "service": "social-media-agent"}


@app.get("/")
async def root():
    return {"status": "ok", "docs": "/docs"}


@app.get("/status")
async def status():
    """Platform connection status for PWA dashboard."""
    try:
        yt = get_channel_status()
        tt = get_tiktok_status()
        return {
            "status": "ok",
            "ai": ai_configured(),
            "youtube": {
                "connected": is_youtube_authenticated(),
                "channel": yt,
            },
            "tiktok": tt,
            "twitter": {"connected": True, "mode": "copy_paste"},
        }
    except Exception as e:
        logger.error("Status check failed: %s", e)
        return {"status": "error", "message": str(e)}


@app.get("/history")
async def history(limit: int = Query(20, ge=1, le=50)):
    try:
        return get_history(limit)
    except Exception as e:
        return {"status": "error", "message": str(e), "history": []}


@app.post("/generate")
async def generate(body: GenerateRequest):
    """
    Trigger full content pipeline: research → write → video (faceless) → optional upload.
    """
    try:
        if not ai_configured():
            raise HTTPException(
                status_code=503,
                detail="AI not configured. Set GEMINI_API_KEY or GROQ_API_KEY.",
            )
        if body.niche not in NICHES:
            raise HTTPException(status_code=400, detail=f"Invalid niche. Use: {NICHES}")
        if body.mode not in MODES:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Use: {MODES}")

        result = run_pipeline(
            niche=body.niche,
            mode=body.mode,
            topic=body.topic,
            post_youtube=body.post_youtube and body.mode == "faceless",
            post_tiktok_flag=body.post_tiktok,
        )
        return {"status": result.get("status", "ok"), "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Generate failed")
        return {"status": "error", "message": str(e)}


@app.post("/upload")
async def upload_video_endpoint(
    file: UploadFile = File(...),
    niche: str = Form("football"),
    topic: Optional[str] = Form(None),
    post_youtube: bool = Form(True),
    post_tiktok: bool = Form(False),
):
    """
    Upload Mode: receive user-recorded video from PWA, then run write + YouTube/TikTok.
    """
    try:
        if not ai_configured():
            raise HTTPException(status_code=503, detail="AI not configured.")

        safe_name = Path(file.filename or "video.mp4").stem[:40]
        save_path = TEMP_VIDEOS_DIR / f"upload_{safe_name}.mp4"

        with open(save_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        result = run_pipeline(
            niche=niche,
            mode="upload",
            topic=topic,
            video_path=str(save_path),
            post_youtube=post_youtube,
            post_tiktok_flag=post_tiktok,
        )
        return {"status": result.get("status", "ok"), "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Upload failed")
        return {"status": "error", "message": str(e)}


@app.get("/auth/login")
async def auth_login(state: str = Query("default")):
    """Start YouTube OAuth — returns redirect URL or redirects browser."""
    result = create_auth_url(state)
    if result.get("status") == "ok" and result.get("auth_url"):
        return RedirectResponse(url=result["auth_url"])
    return result


@app.get("/auth/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: str = Query("default"),
    error: Optional[str] = None,
):
    """OAuth redirect from Google."""
    if error:
        return HTMLResponse(
            f"<h1>Auth failed</h1><p>{error}</p><a href='{FRONTEND_URL}'>Back to app</a>",
            status_code=400,
        )
    if not code:
        return HTMLResponse("<h1>Missing authorization code</h1>", status_code=400)

    result = handle_callback(code, state)
    redirect = result.get("redirect", FRONTEND_URL)
    if result.get("status") == "ok":
        return RedirectResponse(url=f"{redirect}?youtube=connected")
    return HTMLResponse(
        f"<h1>Connection failed</h1><p>{result.get('message')}</p>"
        f"<a href='{FRONTEND_URL}'>Back to app</a>",
        status_code=400,
    )


@app.post("/auth/disconnect")
async def auth_disconnect():
    try:
        return revoke_and_clear()
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=True)
