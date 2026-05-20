# YouTube Upload Skill

## Role
You are a YouTube API expert handling OAuth 
authentication and video uploads for a 
multi-user social media agent.

## When To Use
Use this skill when building tools/youtube.py 
and auth.py

## Step-by-Step Workflow
1. Check if valid OAuth token exists
2. If not, redirect user to /auth/login
3. After OAuth callback, save token server-side
4. Use token to initialize YouTube API client
5. Upload video with full metadata
6. Return YouTube video URL on success

## Required Upload Metadata
- title (max 100 chars)
- description (include hashtags)
- tags (list of strings)
- categoryId (use "22" for People/Blogs)
- privacyStatus: "public"
- madeForKids: false

## OAuth Requirements
- Client type: Web Application
- Scopes needed: 
  youtube.upload
  youtube.readonly
- Store token in backend (never send to frontend)
- Refresh token automatically when expired

## Constraints
- Max file size: 256GB (not an issue for us)
- Use resumable upload for files over 5MB
- Always verify upload success before deleting file
- Handle quota limits (10,000 units/day free)