"""Quick verification (no OAuth/video upload). Run: python scripts/verify.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], label: str) -> bool:
    print(f"\n--- {label} ---")
    r = subprocess.run(cmd, cwd=ROOT)
    ok = r.returncode == 0
    print("PASS" if ok else "FAIL")
    return ok


def main():
    py = sys.executable
    checks = [
        ([py, "-c", "from backend.main import app; print(app.title)"], "Backend import"),
        ([py, "scripts/test_research.py"], "Research"),
        ([py, "scripts/test_twitter.py"], "Twitter"),
        ([py, "scripts/test_tiktok.py"], "TikTok config"),
        ([py, "scripts/test_youtube.py"], "YouTube config"),
    ]
    passed = sum(1 for c, l in checks if run(c, l))

    print("\n--- Writer (Gemini/Groq, may take ~30s) ---")
    r = subprocess.run([py, "scripts/test_writer.py"], cwd=ROOT)
    if r.returncode == 0:
        passed += 1
        print("PASS")
    else:
        print("FAIL or console encoding issue (check status in output)")

    print(f"\n{passed}/{len(checks)+1} checks passed.")
    print("Optional: start backend and run: python scripts/test_api.py")
    return 0 if passed >= len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
