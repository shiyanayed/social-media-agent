"""
Research tool — DuckDuckGo + Wikipedia + Reddit (all free, no API keys).
"""

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 12
REDDIT_UA = "social-media-agent/1.0 (research; contact: local-dev)"

# Subreddits per niche for hot posts
NICHE_SUBREDDITS: dict[str, list[str]] = {
    "football": ["soccer", "PremierLeague"],
    "movies": ["movies", "boxoffice"],
    "anime": ["anime"],
    "crypto": ["cryptocurrency", "Bitcoin"],
}

# Used when web search returns nothing (no API key required)
NICHE_FALLBACK_SUMMARY = {
    "football": (
        "Trending angles: Premier League title race, Champions League knockouts, "
        "transfer rumors, controversial VAR decisions, and post-match hot takes."
    ),
    "movies": (
        "Trending angles: new theatrical releases, streaming hits, trailer drops, "
        "box office surprises, and ranked lists (best sci-fi, horror, etc.)."
    ),
    "anime": (
        "Trending angles: seasonal premieres, episode 1 reactions, power scaling debates, "
        "manga adaptations, and watch-order recommendations."
    ),
    "crypto": (
        "Trending angles: Bitcoin/ETH price action, ETF flows, altcoin rotations, "
        "regulatory headlines, and on-chain metrics."
    ),
}

# Niche-specific base queries (date appended automatically)
NICHE_QUERIES = {
    "football": [
        "football soccer latest news today",
        "premier league match analysis today",
        "champions league hot takes today",
    ],
    "movies": [
        "trending movies this week",
        "new movie trailer reactions today",
        "box office hits today",
    ],
    "anime": [
        "new anime episode reactions today",
        "trending anime recommendations today",
        "anime season premiere news today",
    ],
    "crypto": [
        "bitcoin ethereum price analysis today",
        "crypto market news today",
        "altcoin trending today",
    ],
}


def _normalize_result(r: dict) -> dict[str, str]:
    return {
        "title": r.get("title", ""),
        "snippet": r.get("body", r.get("snippet", "")),
        "url": r.get("href", r.get("url", "")),
    }


def _search_ddgs(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Primary search via ddgs package (free, no API key)."""
    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(_normalize_result(r))
        return results
    except Exception as e:
        logger.debug("ddgs search failed for '%s': %s", query, e)
        return []


def _search_ddg_legacy(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Fallback: duckduckgo-search package."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(_normalize_result(r))
        return results
    except Exception as e:
        logger.debug("duckduckgo_search failed for '%s': %s", query, e)
        return []


def _search_ddg(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Run DuckDuckGo search with ddgs first, legacy package second."""
    results = _search_ddgs(query, max_results)
    if not results:
        results = _search_ddg_legacy(query, max_results)
    return results


def _search_wikipedia(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """Wikipedia opensearch API (free, no key)."""
    try:
        url = (
            "https://en.wikipedia.org/w/api.php"
            f"?action=opensearch&search={quote(query)}&limit={max_results}&format=json"
        )
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": REDDIT_UA})
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 4:
            return []
        titles, descriptions, links = data[1], data[2], data[3]
        results = []
        for title, desc, link in zip(titles, descriptions, links):
            results.append(
                {
                    "title": f"Wikipedia: {title}",
                    "snippet": (desc or "")[:300],
                    "url": link,
                    "source": "wikipedia",
                }
            )
        return results
    except Exception as e:
        logger.debug("Wikipedia search failed for '%s': %s", query, e)
        return []


def _search_reddit(niche: str, topic: str | None = None, max_per_sub: int = 3) -> list[dict[str, str]]:
    """Reddit public JSON feeds (free, no OAuth for read-only hot posts)."""
    subs = NICHE_SUBREDDITS.get(niche, [])
    results: list[dict[str, str]] = []
    headers = {"User-Agent": REDDIT_UA}

    for sub in subs[:2]:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={max_per_sub}"
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                logger.warning("Reddit rate limited for r/%s", sub)
                continue
            resp.raise_for_status()
            children = resp.json().get("data", {}).get("children", [])
            for child in children:
                post = child.get("data", {})
                title = post.get("title", "")
                if not title or post.get("stickied"):
                    continue
                if topic and topic.lower() not in title.lower():
                    # Prefer topic-related posts when user specified a focus
                    continue
                snippet = (post.get("selftext") or "")[:200] or f"Hot on r/{sub}"
                results.append(
                    {
                        "title": f"r/{sub}: {title}",
                        "snippet": snippet,
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "source": "reddit",
                    }
                )
        except Exception as e:
            logger.debug("Reddit fetch failed for r/%s: %s", sub, e)

    # If topic filter removed everything, retry without filter
    if topic and not results:
        return _search_reddit(niche, topic=None, max_per_sub=max_per_sub)

    return results


def _merge_results(
    target: list[dict[str, str]],
    seen: set[str],
    new_items: list[dict[str, str]],
    limit: int = 10,
) -> None:
    """Append unique results by URL."""
    for item in new_items:
        url = item.get("url", "") or item.get("title", "")
        if url in seen:
            continue
        seen.add(url)
        target.append(item)
        if len(target) >= limit:
            break


def research_trending(niche: str, topic: str | None = None) -> dict[str, Any]:
    """
    Research trending topics for a niche.
    Returns structured JSON with findings (max 5 per query, multiple queries).
    """
    niche = niche.lower().strip()
    if niche not in NICHE_QUERIES:
        return {
            "status": "error",
            "message": f"Invalid niche. Choose from: {list(NICHE_QUERIES.keys())}",
        }

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    queries = list(NICHE_QUERIES[niche])

    # Optional custom topic from user/agent
    if topic:
        templates = {
            "football": f"{topic} match analysis {today}",
            "movies": f"{topic} review {today}",
            "anime": f"{topic} episode reaction {today}",
            "crypto": f"{topic} price prediction {today}",
        }
        queries.insert(0, templates.get(niche, f"{topic} {today}"))

    all_results: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    sources_used: list[str] = []

    for q in queries[:2]:
        if len(all_results) >= 5:
            break
        full_query = f"{q} {today}" if today not in q else q
        ddg_items = _search_ddg(full_query, max_results=5)
        if ddg_items:
            sources_used.append("duckduckgo")
        for item in ddg_items:
            item.setdefault("source", "duckduckgo")
        _merge_results(all_results, seen_urls, ddg_items, limit=5)

    # Wikipedia: topic or primary niche query
    wiki_query = topic or queries[0].split(" today")[0]
    wiki_items = _search_wikipedia(wiki_query, max_results=3)
    if wiki_items:
        sources_used.append("wikipedia")
    _merge_results(all_results, seen_urls, wiki_items, limit=10)

    # Reddit: niche hot posts
    reddit_items = _search_reddit(niche, topic)
    if reddit_items:
        sources_used.append("reddit")
    _merge_results(all_results, seen_urls, reddit_items, limit=10)

    if not all_results:
        fallback = NICHE_FALLBACK_SUMMARY.get(niche, "General trending topics in this niche.")
        if topic:
            fallback = f"Focus: {topic}. {fallback}"
        return {
            "status": "ok",
            "niche": niche,
            "topic": topic,
            "findings": [],
            "summary": fallback,
            "source": "fallback",
            "date": today,
        }

    # Build context string for writer
    summary_parts = [f"- {r['title']}: {r['snippet'][:200]}" for r in all_results[:5]]
    summary = "\n".join(summary_parts)

    return {
        "status": "ok",
        "niche": niche,
        "topic": topic,
        "findings": all_results[:10],
        "summary": summary,
        "source": "+".join(dict.fromkeys(sources_used)) or "mixed",
        "date": today,
    }


def research_tool_description() -> str:
    """LangChain tool description."""
    return (
        "Research trending topics for social media. "
        "Input: JSON string with 'niche' (football/movies/anime/crypto) "
        "and optional 'topic'. Returns findings and summary."
    )
