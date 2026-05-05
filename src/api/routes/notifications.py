from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.session import get_db
from src.db.models import (
    Application, ApplicationStatus, HITLReview, Notification,
    NotificationChannel, NotificationStatus, User,
)
from src.auth.middleware import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# Customer-facing notification for HITL review decisions
# ---------------------------------------------------------------------------

_DECISION_LABELS = {
    "approved": "Approved",
    "conditional": "Conditionally Approved",
    "denied": "Denied",
    "escalated": "Under Additional Review",
}

_DECISION_MESSAGES = {
    "approved": "Your loan application has been approved by a bank officer.",
    "denied": "Your loan application was not approved at this time.",
    "conditional": "Your loan application has been conditionally approved. Please check your status page for details.",
    "escalated": "Your application requires additional review.",
}


class NotificationItem(BaseModel):
    application_id: uuid.UUID
    reference_number: Optional[str]
    decision: str
    decision_label: str
    message: str
    reviewed_at: datetime


@router.get("", response_model=list[NotificationItem])
async def get_customer_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return notifications for the authenticated customer.

    A notification is generated for each of the user's applications that has
    been reviewed by an officer (HITLReview exists, status == DECIDED).
    """
    result = await db.execute(
        select(Application)
        .join(HITLReview, HITLReview.application_id == Application.id)
        .where(
            Application.user_id == user.id,
            Application.status == ApplicationStatus.DECIDED,
        )
        .options(selectinload(Application.hitl_review))
        .order_by(HITLReview.reviewed_at.desc())
    )
    applications = result.scalars().all()

    items: list[NotificationItem] = []
    for app in applications:
        review = app.hitl_review
        if not review:
            continue
        decision_val = review.officer_decision.value
        items.append(
            NotificationItem(
                application_id=app.id,
                reference_number=app.reference_number,
                decision=decision_val,
                decision_label=_DECISION_LABELS.get(decision_val, decision_val),
                message=_DECISION_MESSAGES.get(decision_val, "Your application status has been updated."),
                reviewed_at=review.reviewed_at,
            )
        )

    return items


class NotificationSendRequest(BaseModel):
    application_id: str | None = None
    channel: str
    recipient: str
    template_name: str


@router.post("/send")
async def send_notification(payload: NotificationSendRequest, db: AsyncSession = Depends(get_db)):
    """Internal notification dispatch (SMS/email/WhatsApp)."""
    import uuid as _uuid
    notification = Notification(
        application_id=_uuid.UUID(payload.application_id) if payload.application_id else None,
        channel=NotificationChannel(payload.channel),
        template_name=payload.template_name,
        recipient=payload.recipient,
        status=NotificationStatus.SENT,
    )
    db.add(notification)
    await db.flush()

    return {"status": "sent", "notification_id": str(notification.id)}
