"""Test live API (backend must be running). Run: python scripts/test_api.py"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("RENDER_BACKEND_URL", os.getenv("RAILWAY_BACKEND_URL", "http://localhost:8000")).rstrip("/")


def get(path: str):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def post(path: str, body: dict, timeout: int = 120):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    print("Backend:", BASE)
    try:
        ping = get("/ping")
        print("ping:", ping)
        status = get("/status")
        print("ai configured:", status.get("ai"))
        print("youtube:", status.get("youtube", {}).get("connected"))
    except urllib.error.URLError as e:
        print("FAIL: Backend not running.", e)
        print("Start: python -m uvicorn backend.main:app --reload --port 8000")
        return 1

    print("\n--- POST /generate (upload mode, metadata only, fast) ---")
    try:
        gen = post(
            "/generate",
            {
                "niche": "football",
                "mode": "upload",
                "topic": "test",
                "post_youtube": False,
                "post_tiktok": False,
            },
            timeout=300,
        )
        print("status:", gen.get("status"))
        data = gen.get("data") or {}
        content = data.get("content") or {}
        if content.get("title"):
            print("title:", content.get("title"))
        if data.get("twitter", {}).get("tweet"):
            print("tweet:", data.get("twitter", {}).get("tweet")[:120], "...")
        if gen.get("status") == "error" or data.get("status") == "error":
            print("message:", data.get("message") or gen)
            return 1
    except Exception as e:
        print("generate failed:", e)
        return 1

    print("\nAPI test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
