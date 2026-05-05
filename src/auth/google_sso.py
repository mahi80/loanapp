from __future__ import annotations

from urllib.parse import urlencode

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def build_google_auth_url() -> str:
    """Build the Google OAuth2 authorization URL."""
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_user_info(code: str) -> dict | None:
    """Exchange authorization code for Google user info.
    Returns dict with keys: google_id, email, name, picture or None on failure.
    """
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error("google_token_exchange_failed", status=token_resp.status_code)
            return None

        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("google_no_access_token")
            return None

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            logger.error("google_userinfo_failed", status=userinfo_resp.status_code)
            return None

        data = userinfo_resp.json()
        return {
            "google_id": data["id"],
            "email": data["email"],
            "name": data.get("name", ""),
            "picture": data.get("picture"),
        }
