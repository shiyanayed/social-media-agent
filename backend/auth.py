# YouTube OAuth 2.0 web application flow.
# Tokens are stored server-side only (token.json) - never sent to the PWA.

import json
import logging
import os
import random
import string
import time
import base64
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

from backend.config import (
    FRONTEND_URL,
    RAILWAY_BACKEND_URL,
    TOKEN_PATH,
    YOUTUBE_CLIENT_SECRETS_PATH,
    YOUTUBE_SCOPES,
    youtube_configured,
)

logger = logging.getLogger(__name__)

# Removed file‑based PKCE pending store – we rely on the signed state payload.
# Optional KV store (e.g., Redis/Upstash) can be used if PKCE_KV_URL is set.
PKCE_KV_URL = os.getenv("PKCE_KV_URL")
if PKCE_KV_URL:
    try:
        import redis
        _kv_store = redis.from_url(PKCE_KV_URL)
    except Exception as e:
        logger.warning("Redis KV unavailable: %s", e)
        _kv_store = None
else:
    _kv_store = None

def _redirect_uri() -> str:
    """Return the absolute OAuth callback URL for this deployment."""
    base = RAILWAY_BACKEND_URL.rstrip("/")
    return f"{base}/auth/callback"

def _make_code_verifier() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(64))

def _make_state() -> str:
    """Create a URL‑safe state string that also carries the PKCE verifier.
    Includes a random component, a timestamp and the verifier itself.
    """
    rand = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    verifier = _make_code_verifier()
    payload = {"v": verifier, "t": int(time.time()), "r": rand}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

def _extract_state(state: str) -> Optional[dict]:
    """Decode the state created by _make_state(). Returns the payload dict or None."""
    try:
        pad = "=" * (-len(state) % 4)
        data = json.loads(base64.urlsafe_b64decode(state + pad).decode())
        if time.time() - data["t"] > 300:
            return None
        return data
    except Exception:
        return None

def _store_verifier(state: str, verifier: str) -> None:
    if _kv_store:
        try:
            _kv_store.setex(state, 600, verifier)
        except Exception as e:
            logger.warning("Failed to store PKCE verifier in KV: %s", e)

def _remove_verifier(state: str) -> None:
    if _kv_store:
        try:
            _kv_store.delete(state)
        except Exception as e:
            logger.warning("Failed to delete PKCE verifier from KV: %s", e)

def get_credentials() -> Optional[Credentials]:
    if not TOKEN_PATH.is_file():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)
        return creds if creds and creds.valid else None
    except Exception as e:
        logger.error("Failed to load credentials: %s", e)
        return None

def save_credentials(creds: Credentials) -> None:
    try:
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    except Exception as e:
        logger.error("Failed to save token: %s", e)
        raise

def is_youtube_authenticated() -> bool:
    return get_credentials() is not None

def create_auth_url(state: str = "default") -> dict:
    """Start YouTube OAuth – generate a PKCE verifier, embed it in the OAuth state.
    Returns a dict with the auth_url and the generated state.
    """
    if not youtube_configured():
        return {"status": "error", "message": "YouTube client secrets not found."}
    try:
        fresh_state = _make_state()
        payload = _extract_state(fresh_state)
        if not payload:
            raise RuntimeError('Failed to create OAuth state')
        verifier = payload['v']
        flow = Flow.from_client_secrets_file(
            str(YOUTUBE_CLIENT_SECRETS_PATH),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=_redirect_uri(),
        )
        flow.code_verifier = verifier
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=fresh_state,
        )
        _store_verifier(fresh_state, verifier)
        return {'status': 'ok', 'auth_url': auth_url, 'state': fresh_state}
    except Exception as e:
        logger.error("OAuth start failed: %s", e)
        return {"status": "error", "message": str(e)}

def handle_callback(code: str, state: str = "default") -> dict:
    """OAuth redirect from Google – exchange code for tokens using the stored verifier.
    The verifier is retrieved from the state payload (which is signed by us) and also cleared from the KV store if present.
    """
    try:
        payload = _extract_state(state)
        if not payload:
            raise RuntimeError("OAuth state missing or expired")
        verifier = payload['v']
        _remove_verifier(state)
        flow = Flow.from_client_secrets_file(
            str(YOUTUBE_CLIENT_SECRETS_PATH),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=_redirect_uri(),
        )
        flow.code_verifier = verifier
        flow.fetch_token(code=code)
        creds = flow.credentials
        save_credentials(creds)
        return {"status": "ok", "message": "YouTube connected successfully!", "redirect": FRONTEND_URL}
    except Exception as e:
        logger.error("OAuth callback failed: %s", e)
        return {"status": "error", "message": str(e)}

def revoke_and_clear() -> dict:
    try:
        if TOKEN_PATH.is_file():
            TOKEN_PATH.unlink()
        return {"status": "ok", "message": "YouTube disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
