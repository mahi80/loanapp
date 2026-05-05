from __future__ import annotations

import uuid
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Webhook
from src.api.models.schemas import WebhookCreate, WebhookResponse

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

VALID_EVENTS = {"decision.made", "hitl.escalated", "evolution.completed", "application.submitted"}


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(payload: WebhookCreate, db: AsyncSession = Depends(get_db)):
    """Register webhook for event notifications."""
    invalid = set(payload.events) - VALID_EVENTS
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid}")

    secret = secrets.token_hex(32)
    webhook = Webhook(
        url=payload.url,
        events=payload.events,
        secret_hash=hashlib.sha256(secret.encode()).hexdigest(),
        active=True,
    )
    db.add(webhook)
    await db.flush()

    return WebhookResponse(webhook_id=webhook.id, status="active")


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Remove a webhook."""
    result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    return {"status": "deleted"}
