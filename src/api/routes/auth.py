from __future__ import annotations

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import User, UserRole
from src.auth.google_sso import build_google_auth_url, exchange_code_for_user_info
from src.auth.jwt_handler import create_access_token
from src.auth.middleware import get_current_user

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def _get_officer_emails() -> set[str]:
    """Load officer emails from settings (comma-separated env var)."""
    from src.config import get_settings
    raw = get_settings().officer_emails
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


class TokenRequest(BaseModel):
    google_id: str
    email: str
    name: str
    picture: str = ""


@router.post("/token")
async def get_token(req: TokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange Google user info for a backend JWT. Called by Next.js auth callback."""
    try:
        result = await db.execute(select(User).where(User.google_id == req.google_id))
        user = result.scalar_one_or_none()

        if user is None:
            role = UserRole.OFFICER if req.email.lower() in _get_officer_emails() else UserRole.CUSTOMER
            user = User(
                google_id=req.google_id,
                email=req.email,
                name=req.name,
                picture_url=req.picture,
                role=role,
            )
            db.add(user)
            await db.flush()
        elif req.email.lower() in _get_officer_emails() and user.role == UserRole.CUSTOMER:
            # Auto-upgrade to officer if email is in the officer list
            user.role = UserRole.OFFICER

        user.last_login_at = datetime.now(UTC)

        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
        )
        return {"access_token": token, "role": user.role.value}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("auth_token_failed", exc_type=type(exc).__name__, email=req.email)
        raise HTTPException(
            status_code=500,
            detail=f"auth/token error [{type(exc).__name__}]: {str(exc)[:300]}",
        )


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    return RedirectResponse(url=build_google_auth_url())


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback. Creates user if needed, returns JWT."""
    user_info = await exchange_code_for_user_info(code)
    if user_info is None:
        raise HTTPException(status_code=401, detail="Google authentication failed")

    result = await db.execute(
        select(User).where(User.google_id == user_info["google_id"])
    )
    user = result.scalar_one_or_none()

    if user is None:
        role = UserRole.OFFICER if user_info["email"].lower() in _get_officer_emails() else UserRole.CUSTOMER
        user = User(
            google_id=user_info["google_id"],
            email=user_info["email"],
            name=user_info["name"],
            picture_url=user_info.get("picture"),
            role=role,
        )
        db.add(user)
        await db.flush()

    user.last_login_at = datetime.now(UTC)

    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )

    from src.config import get_settings
    settings = get_settings()
    # Set JWT as HttpOnly cookie instead of exposing in URL query string
    response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback",
        status_code=302,
    )
    response.set_cookie(
        key="backend_token",
        value=token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
    return response


@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "picture_url": user.picture_url,
    }


class PromoteRequest(BaseModel):
    email: str


@router.post("/promote")
async def promote_user(
    req: PromoteRequest,
    officer: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Promote a user to officer role. Requires existing officer auth."""
    if officer.role != UserRole.OFFICER:
        raise HTTPException(status_code=403, detail="Only officers can promote users")

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found — they must sign in first")

    user.role = UserRole.OFFICER
    return {"status": "promoted", "email": user.email, "role": user.role.value}
