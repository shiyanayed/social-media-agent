"""Test writer tool independently. Run: python scripts/test_writer.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.writer import write_content

if __name__ == "__main__":
    summary = "Trending: major match recap, transfer rumors, fan reactions."
    result = write_content("football", summary, mode="faceless", topic="Premier League")
    print("status:", result.get("status"))
    if result.get("status") == "ok":
        print("title:", result.get("title"))
        print("script:", (result.get("script") or "")[:200], "...")
        tweet = result.get("tweet") or ""
        print("tweet:", tweet[:120].encode("ascii", errors="replace").decode())
    else:
        print("error:", result.get("message"))
