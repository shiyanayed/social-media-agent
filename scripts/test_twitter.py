"""Test Twitter generator independently. Run: python scripts/test_twitter.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.tools.twitter import generate_tweet

if __name__ == "__main__":
    result = generate_tweet("crypto", "Bitcoin volatility spikes amid ETF news.", topic="BTC")
    print(result)
