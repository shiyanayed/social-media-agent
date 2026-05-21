"""
YouTube OAuth 2.0 web application flow.
Tokens are stored server-side only (token.json) - never sent to the PWA.
"""

import json
import logging
import os
import random
import string
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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

# Store both flow and code_verifier together
_pending_flows: dict[str, dict] = {}


def _redirect_uri() -> str:
    base = RAILWAY_BACKEND_URL.rstrip("/")
    return f"{base}/auth/callback"


def _make_code_verifier() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(64))


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
    if not youtube_configured():
        return {
            "status": "error",
            "message": "YouTube client secrets not found."
        }
    try:
        code_verifier = _make_code_verifier()
        flow = Flow.from_client_secrets_file(
            str(YOUTUBE_CLIENT_SECRETS_PATH),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=_redirect_uri(),
        )
        flow.code_verifier = code_verifier
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        _pending_flows[state] = {
            "flow": flow,
            "code_verifier": code_verifier
        }
        return {"status": "ok", "auth_url": auth_url}
    except Exception as e:
        logger.error("OAuth start failed: %s", e)
        return {"status": "error", "message": str(e)}


def handle_callback(code: str, state: str = "default") -> dict:
    try:
        pending = _pending_flows.pop(state, None)
        if pending:
            flow = pending["flow"]
            code_verifier = pending["code_verifier"]
        else:
            code_verifier = None
            flow = Flow.from_client_secrets_file(
                str(YOUTUBE_CLIENT_SECRETS_PATH),
                scopes=YOUTUBE_SCOPES,
                redirect_uri=_redirect_uri(),
            )
        flow.code_verifier = code_verifier
        flow.redirect_uri = _redirect_uri()
        flow.fetch_token(code=code)
        creds = flow.credentials
        save_credentials(creds)
        return {
            "status": "ok",
            "message": "YouTube connected successfully!",
            "redirect": FRONTEND_URL,
        }
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
