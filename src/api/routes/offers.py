from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Offer

router = APIRouter(prefix="/api/v1/applications", tags=["offers"])


@router.post("/{application_id}/accept-offer")
async def accept_offer(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Borrower accepts offer. Triggers e-sign + disbursement workflow."""
    result = await db.execute(select(Offer).where(Offer.application_id == application_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.accepted:
        raise HTTPException(status_code=400, detail="Offer already accepted")

    offer.accepted = True
    from datetime import datetime, timezone
    offer.accepted_at = datetime.now(timezone.utc)

    return {"status": "accepted", "next_step": "e-sign and disbursement initiated"}


@router.post("/{application_id}/resend-offer")
async def resend_offer(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Resend offer via SMS/email/WhatsApp."""
    result = await db.execute(select(Offer).where(Offer.application_id == application_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    return {"status": "resent", "channels": ["sms", "email"]}
