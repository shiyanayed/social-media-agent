# Troubleshooting

## ERR_CONNECTION_REFUSED

Nothing is listening on that port.

1. **PWA UI** → http://localhost:3000  
   ```powershell
   npx serve frontend -p 3000
   ```

2. **API** → http://localhost:8000  
   ```powershell
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

Or run `.\scripts\start-dev.ps1` and keep both terminals open.

## Generate fails / backend offline

The red banner means `/ping` failed. Restart the API terminal.

## YouTube Connect fails

- Ensure `client_secrets.json` (or `client_secrets.json.json`) exists in project root
- Google Cloud redirect URI must match: `http://localhost:8000/auth/callback`
- Enable YouTube Data API v3

## Faceless video fails

- Install **ffmpeg**: `winget install Gyan.FFmpeg`
- **Close and reopen** PowerShell after install so PATH updates
- Check: `.\scripts\check-ffmpeg.ps1` or `ffmpeg -version`
- Set `PEXELS_API_KEY` in `.env`
- gTTS needs internet

## Research returns empty

DuckDuckGo may rate-limit. Retry later or set a focus topic in the app.

## Old UI after update

Hard refresh (`Ctrl+Shift+R`) or DevTools → Application → Service Workers → Unregister.
