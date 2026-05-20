# FastAPI Backend Skill

## Role
You are a FastAPI expert building a production-ready 
backend for a social media AI agent.

## When To Use
Use this skill when building or editing any file in 
the backend/ folder, especially main.py and auth.py

## Step-by-Step Workflow
1. Always use async functions for all routes
2. Use APIRouter to separate route groups
3. Always include CORS middleware for PWA access
4. Return clear JSON responses with status fields
5. Wrap all routes in try/except blocks
6. Use Pydantic models for all request bodies

## Required Routes To Build
POST /generate     - trigger content generation
POST /upload       - receive video file from PWA
GET  /auth/login   - start YouTube OAuth
GET  /auth/callback - handle OAuth redirect
GET  /status       - check all platform connections
GET  /history      - return recent posts

## Constraints
- Never block the event loop (use async/await)
- Always validate incoming data with Pydantic
- CORS must allow the Vercel frontend URL
- All errors must return JSON, never plain text