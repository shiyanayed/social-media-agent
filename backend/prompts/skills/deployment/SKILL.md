# Deployment Skill

## Role
You are a DevOps expert deploying a split-architecture 
app: FastAPI backend on Railway, PWA frontend on Vercel.

## When To Use
Use this skill when creating railway.json, vercel.json,
.gitignore, and README.md

## Railway Setup (Backend)
1. Create railway.json in project root
2. Set start command: 
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
3. Set environment variables in Railway dashboard:
   - GEMINI_API_KEY
   - GROQ_API_KEY
   - PEXELS_API_KEY
   - YOUTUBE_CLIENT_SECRETS (paste JSON content)
4. Connect to GitHub repo main branch
5. Copy Railway URL → paste in Vercel env vars

## Vercel Setup (Frontend)
1. Create vercel.json pointing to frontend/ folder
2. Set environment variable:
   BACKEND_URL = your Railway URL
3. Connect to GitHub repo main branch
4. app.js must read BACKEND_URL dynamically

## .gitignore Must Include
- .env
- client_secrets.json
- token.json
- __pycache__/
- *.pyc
- temp_videos/
- node_modules/

## Constraints
- Never commit .env or client_secrets.json
- Railway free tier sleeps after inactivity
- Add a /ping route to keep Railway awake
- Vercel only serves static files (no Python)