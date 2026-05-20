"""Test TikTok API configuration. Run: python scripts/test_tiktok.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.tiktok import get_tiktok_status, tiktok_tool_description

if __name__ == "__main__":
    print(get_tiktok_status())
    print("\nTool:", tiktok_tool_description()[:120], "...")
