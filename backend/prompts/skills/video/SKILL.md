# Faceless Video Creation Skill

## Role
You are a video automation expert using free Python 
tools to create faceless YouTube videos automatically.

## When To Use
Use this skill when building tools/video.py

## Step-by-Step Workflow
1. Receive script text from writer.py
2. Split script into sentences/sections
3. Generate MP3 voiceover using gTTS
4. Search Pexels API for relevant stock clips
5. Download stock clips temporarily
6. Assemble clips + voiceover using MoviePy
7. Add text overlay (title/captions) with MoviePy
8. Export final MP4 file
9. Pass file path to youtube.py for upload
10. Delete temporary files after upload

## Pexels Search Strategy
- Extract 3-5 keywords from script
- Search one keyword per video section
- Download 5-10 second clips per section
- Match clip duration to voiceover length

## Video Specs
- Resolution: 1080x1920 (YouTube Shorts) or
  1920x1080 (regular YouTube)
- Format: MP4 H.264
- Audio: 44100Hz stereo

## Constraints
- Always clean up temp files
- Handle Pexels API rate limits (200 req/hour)
- gTTS requires internet connection
- MoviePy requires ffmpeg installed
- Keep videos under 15 minutes