# Product Roadmap — Paid Release Ideas

Vision: sell access to a **niche social media AI agent** that researches, writes, renders faceless video, and posts (or prepares posts) for creators who do not want to be on camera.

## Tier 1 — Visual & UX (high impact, low cost)

- Custom brand kit: logo, colors, typography per customer workspace
- Onboarding wizard (pick niche → connect platforms → first generate)
- Rich analytics dashboard: posts, views (YouTube API), engagement
- Dark/light theme toggle
- Animated Lottie or CSS mascot during long video renders
- In-app script editor before video render (human tweak)
- Preview card mimicking YouTube Shorts / TikTok safe zones

## Tier 2 — Monetization mechanics

- **Freemium:** 3 generates/day free; unlimited on Pro
- **Stripe** checkout (Railway backend + webhook)
- Per-niche add-ons (Crypto pack, Football pack)
- Team seats: one OAuth per channel, multiple users
- White-label: custom domain PWA + logo for agencies

## Tier 3 — Product depth

- Scheduled posts (cron + queue table)
- A/B titles — Gemini generates 3 titles, user picks
- Auto hashtags from live trends (improved research)
- Multi-language voiceover (gTTS langs)
- B-roll from Pexels + AI image slides (Gemini Imagen optional)
- Content calendar view in PWA
- Email digest of weekly performance

## Tier 4 — Infrastructure for scale

- Redis job queue for video renders (no HTTP timeout)
- S3/R2 storage for temp videos
- Multi-tenant auth (Clerk/Supabase) instead of single token file
- Rate limits per API key
- Admin panel for usage billing

## Legal & trust (before charging money)

- Terms of Service + Privacy Policy
- Disclaimer: user owns content; platform ToS compliance
- YouTube/TikTok API compliance and quota monitoring
- GDPR: data export/delete for EU users

## Pricing sketch (example)

| Plan | Price | Includes |
|------|-------|----------|
| Starter | $19/mo | 30 faceless videos, 1 niche, X copy |
| Pro | $49/mo | Unlimited metadata, 4 niches, TikTok |
| Agency | $149/mo | 5 channels, white-label, priority queue |

## Technical debt to clear before launch

- [ ] E2E test: faceless video without YouTube (local MP4 only)
- [ ] Deploy Railway + Vercel with production OAuth URLs
- [ ] Replace DDG with paid Serper optional tier for reliable research
- [ ] Job status WebSocket for 5–10 min video builds
