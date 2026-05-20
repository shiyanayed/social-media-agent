# Research Tool Skill

## Role
You are a web research expert using DuckDuckGo 
to find trending topics for social media content.

## When To Use
Use this skill when building tools/research.py

## Step-by-Step Workflow
1. Receive niche as input (football/movies/anime/crypto)
2. Build search queries per niche:
   Football: "[team name] latest news today"
   Movies: "trending movies [current month]"
   Anime: "new anime episode reactions today"
   Crypto: "[coin] price analysis today"
3. Run DuckDuckGo search (use duckduckgo-search lib)
4. Extract top 5 results (title + snippet + url)
5. Pass results to writer.py as context
6. Return structured JSON with findings

## Search Query Templates
Football: "{topic} match analysis {date}"
Movies: "{movie} review {year}"
Anime: "{anime} episode {number} reaction"
Crypto: "{coin} price prediction {date}"

## Data sources (in order)
1. DuckDuckGo via `ddgs` (then legacy `duckduckgo-search`)
2. Wikipedia opensearch API (free, no key)
3. Reddit public hot.json per niche subreddit (free, User-Agent required)
4. Niche fallback text if all empty

## Constraints
- Use ddgs / duckduckgo-search (free, no API key)
- Max 5 search results per query
- Always include the date in queries
- Handle connection timeouts gracefully
- Never scrape full article content