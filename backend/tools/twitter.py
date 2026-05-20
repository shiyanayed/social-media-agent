"""
X/Twitter content generator — copy/paste workflow (no API posting).
Uses writer output or generates standalone tweets from research.
"""

import logging
from typing import Any

from backend.tools.writer import write_content

logger = logging.getLogger(__name__)


def generate_tweet(
    niche: str,
    research_summary: str = "",
    topic: str | None = None,
    existing_tweet: str | None = None,
) -> dict[str, Any]:
    """
    Return tweet text for manual copy/paste to X.
    Reuses writer if no existing_tweet provided.
    """
    try:
        if existing_tweet:
            tweet = existing_tweet[:280]
            return {
                "status": "ok",
                "tweet": tweet,
                "platform": "x",
                "instructions": "Copy the tweet below and paste into X/Twitter app.",
            }

        content = write_content(
            niche=niche,
            research_summary=research_summary,
            mode="upload",
            topic=topic,
        )
        if content.get("status") == "error":
            return content

        tweet = str(content.get("tweet", ""))[:280]
        if not tweet:
            tweet = f"🔥 New {niche} content dropping soon! #trending #{niche}"

        return {
            "status": "ok",
            "tweet": tweet,
            "title": content.get("title"),
            "platform": "x",
            "instructions": "Copy the tweet below and paste into X/Twitter app.",
        }
    except Exception as e:
        logger.error("Tweet generation failed: %s", e)
        return {"status": "error", "message": str(e)}


def format_copy_block(tweet: str, title: str | None = None) -> str:
    """Human-readable block for PWA display."""
    lines = ["=== X / Twitter (copy & paste) ===", tweet]
    if title:
        lines.insert(1, f"Video: {title}")
    return "\n".join(lines)


def twitter_tool_description() -> str:
    return (
        "Generate X/Twitter copy-paste post. "
        "Input: JSON with niche, research_summary, optional topic or existing_tweet."
    )
