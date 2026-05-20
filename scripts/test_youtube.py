"""Test YouTube auth + channel status. Run: python scripts/test_youtube.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth import is_youtube_authenticated
from backend.config import YOUTUBE_CLIENT_SECRETS_PATH, youtube_configured
from backend.tools.youtube import get_channel_status


def main():
    print("client_secrets file:", YOUTUBE_CLIENT_SECRETS_PATH, "exists:", youtube_configured())
    print("authenticated:", is_youtube_authenticated())
    if not is_youtube_authenticated():
        print("\nConnect YouTube: open http://localhost:8000/auth/login in your browser")
        return 0
    status = get_channel_status()
    print("channel status:", status)
    return 0 if status.get("connected") else 1


if __name__ == "__main__":
    raise SystemExit(main())
