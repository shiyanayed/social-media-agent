"""
Content writer using Gemini 2.5 Flash (primary) and Groq (fallback).
Uses official free-tier SDKs — no LangChain dependency.
"""

import json
import logging
from typing import Any

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    NICHE_TONES,
)

logger = logging.getLogger(__name__)

NICHE_SYSTEM = {
    "football": "You are a passionate football analyst. Give hot takes and match analysis.",
    "movies": "You are a witty movie critic. Be entertaining and sharp.",
    "anime": "You are an expressive anime fan. React with energy and recommendations.",
    "crypto": "You are an analytical crypto commentator. Be urgent and data-focused.",
}


def _call_gemini(prompt: str, system: str) -> str:
    """Google Gemini via official google-genai SDK (free tier)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.8,
        ),
    )
    text = response.text
    if not text:
        raise RuntimeError("Gemini returned empty response")
    return text.strip()


def _call_groq(prompt: str, system: str) -> str:
    """Groq via official SDK (free tier fallback)."""
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        timeout=60,
    )
    text = completion.choices[0].message.content
    if not text:
        raise RuntimeError("Groq returned empty response")
    return text.strip()


def _invoke_llm(prompt: str, system: str) -> str:
    """Try Gemini first, fall back to Groq on failure."""
    if GEMINI_API_KEY:
        try:
            return _call_gemini(prompt, system)
        except Exception as e:
            logger.warning("Gemini failed, trying Groq: %s", e)

    if GROQ_API_KEY:
        try:
            return _call_groq(prompt, system)
        except Exception as e:
            logger.error("Groq also failed: %s", e)
            raise

    raise RuntimeError("No AI API keys configured (GEMINI_API_KEY or GROQ_API_KEY)")


def _parse_json_from_llm(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "script": text,
            "title": "Untitled",
            "description": text[:500],
            "tags": [],
            "tweet": text[:280],
        }


def write_content(
    niche: str,
    research_summary: str,
    mode: str = "faceless",
    topic: str | None = None,
) -> dict[str, Any]:
    """
    Generate full content package: script, YouTube metadata, tweet.
    mode: 'faceless' (short-form script) or 'upload' (metadata for user video).
    """
    niche = niche.lower().strip()
    tone = NICHE_TONES.get(niche, "Engaging social media creator")
    system = NICHE_SYSTEM.get(niche, "You are a social media content creator.")

    mode_hint = (
        "Write a 60-90 second voiceover script for a faceless YouTube Short (vertical)."
        if mode == "faceless"
        else "User will record their own video. Provide script as talking points plus full metadata."
    )

    skill_extra = ""
    try:
        from backend.prompts.loader import get_skill_prompt

        skill_extra = get_skill_prompt("writer")
        if skill_extra:
            skill_extra = f"\nSkill guidelines:\n{skill_extra}\n"
    except Exception:
        pass

    prompt = f"""{system}
{skill_extra}
Tone: {tone}
Niche: {niche}
Mode: {mode}
{mode_hint}

Research context:
{research_summary or 'General trending topics in this niche.'}
{f'Focus topic: {topic}' if topic else ''}

Respond with ONLY valid JSON (no markdown outside JSON):
{{
  "script": "full voiceover or talking points, 150-300 words",
  "title": "YouTube title max 100 chars",
  "description": "YouTube description with hashtags",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "tweet": "X/Twitter post max 280 chars with hashtags",
  "tiktok_caption": "TikTok caption with hashtags",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}
"""

    try:
        raw = _invoke_llm(prompt, system)
        data = _parse_json_from_llm(raw)
        data["status"] = "ok"
        data["niche"] = niche
        data["mode"] = mode
        if data.get("title"):
            data["title"] = str(data["title"])[:100]
        if data.get("tweet"):
            data["tweet"] = str(data["tweet"])[:280]
        return data
    except Exception as e:
        logger.error("Content generation failed: %s", e)
        return {"status": "error", "message": str(e)}


def writer_tool_description() -> str:
    return (
        "Write social media content from research. "
        "Input: JSON with niche, research_summary, mode (faceless/upload), optional topic."
    )
