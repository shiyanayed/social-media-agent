# Social Media AI Agent

Progressive Web App (PWA) + FastAPI backend that researches trends, writes niche content, creates faceless videos, and posts to YouTube, TikTok, and X (copy/paste).

## Architecture

| Layer | Host | Stack |
|-------|------|--------|
| Frontend PWA | Vercel | Vanilla HTML/CSS/JS |
| Backend API | Railway | FastAPI, Gemini/Groq SDKs |

## Features

- **Niches:** Football, Movies, Anime, Crypto (unique tones)
- **Faceless mode:** DuckDuckGo → Gemini script → gTTS + Pexels + MoviePy → YouTube upload
- **Upload mode:** Metadata + user-recorded video → YouTube upload
- **X/Twitter:** Generated tweet for manual copy/paste
- **TikTok:** Auto-post when API token is configured

## Project structure

```
social-media-agent/
├── backend/          # FastAPI + agent + tools
├── frontend/         # PWA (installable on iOS/Android)
├── .env              # Local secrets (never commit)
├── railway.json      # Railway deploy
└── vercel.json       # Vercel deploy (frontend only)
```

## Local setup

### 1. Clone and environment

```bash
cd social-media-agent
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r backend/requirements.txt
```

Copy `.env` and fill in keys:

```env
GEMINI_API_KEY=...
GROQ_API_KEY=...
PEXELS_API_KEY=...
YOUTUBE_CLIENT_SECRETS=client_secrets.json
RAILWAY_BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 2. YouTube OAuth

1. [Google Cloud Console](https://console.cloud.google.com/) → APIs → enable **YouTube Data API v3**
2. OAuth consent screen → add test users
3. Credentials → **Web application**
4. Redirect URI: `http://localhost:8000/auth/callback` (and your Railway URL in production)
5. Download JSON → save as `client_secrets.json` in project root

### 3. System dependencies (video)

**Research** uses DuckDuckGo + **Wikipedia** + **Reddit** (no API keys).

Install **ffmpeg** (required by MoviePy):

- Windows: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org)
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### 4. Run backend

From project root:

```powershell
# Windows (if `uvicorn` is not on PATH):
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 5. YouTube client secrets filename

If your Google download is named `client_secrets.json.json`, either rename it to `client_secrets.json` or set in `.env`:

```env
YOUTUBE_CLIENT_SECRETS=client_secrets.json.json
```

### 6. Test tools independently

```powershell
python scripts/test_research.py
python scripts/test_writer.py
python scripts/test_twitter.py
python scripts/test_video.py
python scripts/test_youtube.py
python scripts/test_tiktok.py
python scripts/test_api.py   # requires backend on :8000
.\scripts\run-all-tests.ps1
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for connection errors and common fixes.

For paid-release ideas see [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md).

Quick verify (no OAuth): `python scripts/verify.py`

### 7. Run frontend

Serve `frontend/` with any static server, e.g.:

```bash
npx serve frontend -p 3000
```

Open http://localhost:3000 — `frontend/config.js` already points to `http://localhost:8000`.

**One-command dev (Windows):**

```powershell
.\scripts\start-dev.ps1
```

### 6. Connect YouTube

In the PWA, tap **Connect** under YouTube, or open:

`http://localhost:8000/auth/login`

## Railway deployment (backend)

1. Push repo to GitHub
2. [Railway](https://railway.app) → New Project → Deploy from GitHub → `main`
3. Set root directory to repo root (uses `railway.json`)
4. Environment variables:
   - `GEMINI_API_KEY`, `GROQ_API_KEY`, `PEXELS_API_KEY`
   - `YOUTUBE_CLIENT_SECRETS` — paste full JSON content OR upload `client_secrets.json` via volume
   - `RAILWAY_BACKEND_URL` — your Railway public URL
   - `FRONTEND_URL` — your Vercel URL
   - TikTok (optional): `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`
5. Update Google OAuth redirect URI: `https://YOUR-APP.up.railway.app/auth/callback`

`/ping` keeps the service warm on free tier (optional cron).

## Vercel deployment (frontend)

1. Import GitHub repo on [Vercel](https://vercel.com)
2. `vercel.json` serves the `frontend/` folder
3. Set env var `BACKEND_URL` = your Railway URL (optional; users can also enter URL in app)
4. Add to `index.html` if desired:

```html
<meta name="backend-url" content="https://your-app.up.railway.app" />
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ping` | Health check |
| GET | `/status` | Platform connections |
| GET | `/history` | Recent posts |
| POST | `/generate` | Run agent pipeline |
| POST | `/upload` | Upload mode video + metadata |
| GET | `/auth/login` | Start YouTube OAuth |
| GET | `/auth/callback` | OAuth redirect |

## Skills (agent prompts)

Domain skills live in `backend/prompts/skills/`:

- `fastapi`, `langchain`, `research`, `video`, `youtube`, `pwa`, `deployment`

## Security

- Never commit `.env`, `client_secrets.json`, or `token.json`
- OAuth tokens stay on the server only
- PWA does not store API keys in `localStorage`

## License

MIT — use free APIs responsibly and follow each platform’s terms of service.
# social-media-agent
