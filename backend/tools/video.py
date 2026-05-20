"""
Faceless video creation: gTTS voiceover + Pexels stock footage + MoviePy assembly.
Exports vertical 1080x1920 MP4 for YouTube Shorts.
"""

import logging
import re
import uuid
from pathlib import Path
from typing import Any

import requests

from backend.config import PEXELS_API_KEY, TEMP_VIDEOS_DIR

logger = logging.getLogger(__name__)

# YouTube Shorts vertical
VIDEO_SIZE = (1080, 1920)
PEXELS_API = "https://api.pexels.com/videos/search"


def _extract_keywords(script: str, extra: list[str] | None = None) -> list[str]:
    """Pull 3-5 keywords from script for Pexels searches."""
    words = re.findall(r"[a-zA-Z]{4,}", script.lower())
    stop = {"that", "this", "with", "from", "have", "your", "about", "they", "what"}
    unique = []
    for w in words:
        if w not in stop and w not in unique:
            unique.append(w)
        if len(unique) >= 5:
            break
    if extra:
        for k in extra:
            if k and k not in unique:
                unique.insert(0, k.lower())
    return unique[:5] or ["nature", "city", "technology"]


def _generate_voiceover(script: str, output_path: Path) -> dict[str, Any]:
    """Convert script to MP3 using gTTS."""
    try:
        from gtts import gTTS

        tts = gTTS(text=script[:5000], lang="en", slow=False)
        tts.save(str(output_path))
        return {"status": "ok", "path": str(output_path)}
    except Exception as e:
        logger.error("gTTS failed: %s", e)
        return {"status": "error", "message": str(e)}


def _search_pexels_video(query: str, per_page: int = 3) -> list[str]:
    """Return list of Pexels video file URLs (HD preferred)."""
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY not set")
        return []
    try:
        resp = requests.get(
            PEXELS_API,
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": per_page, "orientation": "portrait"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        urls = []
        for video in data.get("videos", []):
            files = video.get("video_files", [])
            # Prefer vertical / medium quality
            best = sorted(files, key=lambda f: f.get("height", 0), reverse=True)
            for f in best:
                if f.get("link"):
                    urls.append(f["link"])
                    break
        return urls
    except Exception as e:
        logger.warning("Pexels search failed for '%s': %s", query, e)
        return []


def _download_clip(url: str, dest: Path) -> bool:
    """Download a stock video clip to disk."""
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest.is_file() and dest.stat().st_size > 0
    except Exception as e:
        logger.warning("Clip download failed: %s", e)
        return False


def create_faceless_video(
    script: str,
    title: str = "",
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """
    Full pipeline: TTS → Pexels clips → MoviePy merge → MP4 path.
    """
    job_id = uuid.uuid4().hex[:8]
    work_dir = TEMP_VIDEOS_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    audio_path = work_dir / "voiceover.mp3"
    output_path = work_dir / "final.mp4"

    try:
        # 1. Voiceover
        voice = _generate_voiceover(script, audio_path)
        if voice.get("status") == "error":
            return voice

        # 2. Stock clips
        kws = _extract_keywords(script, keywords)
        clip_paths: list[Path] = []
        for i, kw in enumerate(kws[:4]):
            urls = _search_pexels_video(kw, per_page=2)
            for j, url in enumerate(urls[:1]):
                dest = work_dir / f"clip_{i}_{j}.mp4"
                if _download_clip(url, dest):
                    clip_paths.append(dest)
                if len(clip_paths) >= 4:
                    break
            if len(clip_paths) >= 4:
                break

        if not clip_paths:
            return {
                "status": "error",
                "message": "No stock footage downloaded. Check PEXELS_API_KEY.",
            }

        # 3. Assemble with MoviePy
        result = _assemble_video(clip_paths, audio_path, output_path, title)
        if result.get("status") == "error":
            return result

        return {
            "status": "ok",
            "video_path": str(output_path),
            "work_dir": str(work_dir),
            "job_id": job_id,
        }
    except Exception as e:
        logger.error("Video creation failed: %s", e)
        return {"status": "error", "message": str(e)}


def _assemble_video(
    clip_paths: list[Path],
    audio_path: Path,
    output_path: Path,
    title: str,
) -> dict[str, Any]:
    """Merge clips to match audio duration; export MP4."""
    try:
        from moviepy.editor import (
            AudioFileClip,
            CompositeVideoClip,
            TextClip,
            VideoFileClip,
            concatenate_videoclips,
        )

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        clips = []
        for p in clip_paths:
            try:
                vc = VideoFileClip(str(p))
                clips.append(vc)
            except Exception as e:
                logger.warning("Skip clip %s: %s", p, e)

        if not clips:
            return {"status": "error", "message": "No valid video clips to assemble"}

        # Loop/trim clips to fill audio duration
        per_clip = duration / len(clips)
        processed = []
        for vc in clips:
            sub = vc.subclip(0, min(per_clip, vc.duration))
            sub = sub.resize(VIDEO_SIZE)
            processed.append(sub)

        video = concatenate_videoclips(processed, method="compose")
        if video.duration < duration:
            video = video.loop(duration=duration)
        else:
            video = video.subclip(0, duration)

        video = video.set_audio(audio)

        # Optional title overlay (first 3 seconds)
        if title:
            try:
                txt = (
                    TextClip(
                        title[:60],
                        fontsize=48,
                        color="white",
                        font="Arial-Bold",
                        stroke_color="black",
                        stroke_width=2,
                    )
                    .set_position(("center", 0.15), relative=True)
                    .set_duration(min(3, duration))
                )
                video = CompositeVideoClip([video, txt])
            except Exception as e:
                logger.warning("Text overlay skipped: %s", e)

        video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            logger=None,
        )

        # Cleanup MoviePy resources
        audio.close()
        for c in clips:
            c.close()
        video.close()

        return {"status": "ok", "path": str(output_path)}
    except Exception as e:
        logger.error("MoviePy assembly failed: %s", e)
        return {"status": "error", "message": str(e)}


def cleanup_work_dir(work_dir: str | Path) -> None:
    """Delete temporary files after successful upload."""
    try:
        import shutil

        path = Path(work_dir)
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        logger.warning("Cleanup failed: %s", e)


def video_tool_description() -> str:
    return (
        "Create a faceless video from a script. "
        "Input: JSON with script, optional title and keywords. Returns video_path."
    )
