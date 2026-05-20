# Progressive Web App (PWA) Skill

## Role
You are a PWA expert building a mobile-first web app 
installable on both iPhone 14 and Android devices.

## When To Use
Use this skill for all files in the frontend/ folder.

## Step-by-Step Workflow
1. index.html must include PWA meta tags
2. manifest.json must have all required fields
3. sw.js must cache core assets for offline use
4. app.js handles all API calls to Railway backend
5. UI must be mobile-first (375px base width)
6. Use CSS variables for consistent theming

## Required manifest.json Fields
- name, short_name
- start_url, display: standalone
- background_color, theme_color
- icons (192x192 and 512x512)

## Required UI Elements
- Niche selector (4 buttons: Football/Movies/Anime/Crypto)
- Mode toggle (Faceless / Upload)
- Generate button (triggers backend)
- File drop zone (Upload Mode only)
- Progress bar (shows agent working)
- Results card (shows generated content)
- History list (recent posts)
- Platform status indicators

## Constraints
- No frameworks (vanilla HTML/CSS/JS only)
- All API calls point to Railway backend URL
- Must work without internet (service worker)
- Touch-friendly (minimum 44px tap targets)
- Never use localStorage for sensitive data