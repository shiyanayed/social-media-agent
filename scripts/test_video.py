"""Test video tool (voice + optional full assemble). Run: python scripts/test_video.py"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import PEXELS_API_KEY


def main():
    print("PEXELS_API_KEY:", "set" if PEXELS_API_KEY else "missing")
    ffmpeg = shutil.which("ffmpeg")
    print("ffmpeg:", ffmpeg or "NOT FOUND (install for full video)")

    from backend.tools.video import _generate_voiceover

    work = Path(__file__).resolve().parent.parent / "temp_videos" / "test_voice"
    work.mkdir(parents=True, exist_ok=True)
    mp3 = work / "test.mp3"
    script = "This is a quick test of the social media agent voiceover system."

    print("\n--- gTTS voiceover ---")
    voice = _generate_voiceover(script, mp3)
    print(voice)
    if voice.get("status") != "ok":
        return 1

    if not ffmpeg:
        print("\nSkipping MoviePy assemble (no ffmpeg). Voice test passed.")
        return 0

    if not PEXELS_API_KEY:
        print("\nSkipping full video (no PEXELS_API_KEY). Voice test passed.")
        return 0

    print("\n--- Full faceless video (may take several minutes) ---")
    from backend.tools.video import create_faceless_video

    result = create_faceless_video(script, "Test Video", ["city", "technology"])
    print("status:", result.get("status"))
    if result.get("video_path"):
        print("video:", result.get("video_path"))
    if result.get("status") == "error":
        print("error:", result.get("message"))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
