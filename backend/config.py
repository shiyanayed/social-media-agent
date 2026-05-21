"""
Central configuration: loads all settings from environment variables.
Never hardcode API keys — use .env locally and Railway/Vercel dashboards in production.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# --- AI ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Media / APIs ---
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

# --- YouTube OAuth ---
YOUTUBE_CLIENT_SECRETS: str = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
YOUTUBE_CLIENT_SECRETS_JSON: str = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON", "")
# Resolve relative path from project root (or write JSON from Railway env)
_secrets_path = Path(YOUTUBE_CLIENT_SECRETS)
if not _secrets_path.is_absolute():
    _secrets_path = _ROOT / _secrets_path
if YOUTUBE_CLIENT_SECRETS_JSON and not _secrets_path.is_file():
    try:
        _secrets_path.write_text(YOUTUBE_CLIENT_SECRETS_JSON, encoding="utf-8")
    except Exception:
        pass
YOUTUBE_CLIENT_SECRETS_PATH: Path = _secrets_path
TOKEN_PATH: Path = _ROOT / "token.json"
# Updated list of scopes includes OpenID and userinfo scopes required by Google
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

# --- TikTok ---
TIKTOK_CLIENT_KEY: str = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")

# --- Deployment ---
BACKEND_URL: str = os.getenv("RENDER_BACKEND_URL", os.getenv("RAILWAY_BACKEND_URL", "http://localhost:8000"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
PORT: int = int(os.getenv("PORT", "8000"))

# --- Paths ---
TEMP_VIDEOS_DIR: Path = _ROOT / "temp_videos"
HISTORY_FILE: Path = _ROOT / "backend" / "data" / "history.json"

# --- Niches ---
NICHES = ("football", "movies", "anime", "crypto")
MODES = ("faceless", "upload")

NICHE_TONES = {
    "football": "Passionate, opinionated — match analysis, hot takes, news",
    "movies": "Entertaining, witty — reviews, trailers, rankings",
    "anime": "Fan-focused, expressive — episode reactions, recommendations",
    "crypto": "Analytical, urgent — market moves, news, commentary",
}

# Ensure temp and data directories exist
TEMP_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def youtube_configured() -> bool:
    """True if client secrets file exists."""
    return YOUTUBE_CLIENT_SECRETS_PATH.is_file()


def tiktok_configured() -> bool:
    """True if TikTok credentials are set."""
    return bool(TIKTOK_ACCESS_TOKEN and TIKTOK_CLIENT_KEY)


def ai_configured() -> bool:
    """True if at least one LLM provider is configured."""
    return bool(GEMINI_API_KEY or GROQ_API_KEY)
