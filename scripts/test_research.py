"""Test research tool independently. Run: python scripts/test_research.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.research import research_trending

if __name__ == "__main__":
    for niche in ("football", "crypto"):
        print(f"\n=== {niche} ===")
        result = research_trending(niche)
        print("status:", result.get("status"))
        print("sources:", result.get("source"))
        print("findings:", len(result.get("findings") or []))
        print("summary:", (result.get("summary") or "")[:300])
