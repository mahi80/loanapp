from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Application, Conversation, CreditDecision, Document, Offer, User
from src.auth.middleware import get_current_user

router = APIRouter(prefix="/api/v1/status", tags=["status"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ApplicationListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    reference_number: Optional[str]
    loan_amount: float
    loan_type: str
    status: str
    current_phase: Optional[str]
    decision: Optional[str]
    conversation_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class PhaseItem(BaseModel):
    phase: str
    completed_at: Optional[str]


class DocumentItem(BaseModel):
    type: str
    status: str
    uploaded_at: datetime


class DecisionDetail(BaseModel):
    result: str
    reasons: list[str]
    confidence: float
    decided_at: datetime


class OfferDetail(BaseModel):
    interest_rate: float
    emi_amount: float
    tenure_months: Optional[int]
    processing_fee: float
    total_cost: float
    accepted: bool


class ApplicationDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    reference_number: Optional[str]
    loan_amount: float
    loan_type: str
    tenure_months: Optional[int]
    status: str
    phase_history: list[PhaseItem]
    current_phase: Optional[str]
    documents: list[DocumentItem]
    decision: Optional[DecisionDetail]
    offer: Optional[OfferDetail]
    conversation_id: Optional[uuid.UUID]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/applications", response_model=list[ApplicationListItem])
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all applications for the authenticated user, newest first."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user.id)
        .options(selectinload(Application.decision))
        .order_by(Application.created_at.desc())
    )
    applications = result.scalars().all()

    # Batch-load conversations for all apps in one query
    app_ids = [app.id for app in applications]
    conv_result = await db.execute(
        select(Conversation).where(Conversation.application_id.in_(app_ids))
    ) if app_ids else None
    conv_map: dict = {}
    if conv_result:
        for conv in conv_result.scalars().all():
            conv_map[conv.application_id] = conv

    items: list[ApplicationListItem] = []
    for app in applications:
        current_phase: Optional[str] = None
        if app.phase_history:
            last = app.phase_history[-1]
            current_phase = last.get("phase") if isinstance(last, dict) else None

        conversation = conv_map.get(app.id)
        items.append(
            ApplicationListItem(
                id=app.id,
                reference_number=app.reference_number,
                loan_amount=float(app.loan_amount),
                loan_type=app.loan_type.value,
                status=app.status.value,
                current_phase=current_phase,
                decision=app.decision.decision.value if app.decision else None,
                conversation_id=conversation.id if conversation else None,
                created_at=app.created_at,
                updated_at=app.updated_at,
            )
        )

    return items


@router.get("/applications/{application_id}", response_model=ApplicationDetail)
async def get_application_detail(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full detail for the status page — verifies ownership."""
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if app is None or app.user_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    # Conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.application_id == app.id)
    )
    conversation = conv_result.scalar_one_or_none()

    # Documents
    docs_result = await db.execute(
        select(Document).where(Document.application_id == app.id)
    )
    documents = docs_result.scalars().all()

    # CreditDecision
    dec_result = await db.execute(
        select(CreditDecision).where(CreditDecision.application_id == app.id)
    )
    credit_decision = dec_result.scalar_one_or_none()

    # Offer
    offer_result = await db.execute(
        select(Offer).where(Offer.application_id == app.id)
    )
    offer = offer_result.scalar_one_or_none()

    # Build phase_history list
    phase_history: list[PhaseItem] = []
    if app.phase_history:
        for entry in app.phase_history:
            if isinstance(entry, dict):
                phase_history.append(
                    PhaseItem(
                        phase=entry.get("phase", ""),
                        completed_at=entry.get("completed_at"),
                    )
                )

    # Derive current_phase
    current_phase: Optional[str] = phase_history[-1].phase if phase_history else None

    # Build document list
    document_items = [
        DocumentItem(
            type=d.type.value,
            status=d.ocr_status.value,
            uploaded_at=d.uploaded_at,
        )
        for d in documents
    ]

    # Build decision detail
    decision_detail: Optional[DecisionDetail] = None
    if credit_decision:
        reasons = (
            credit_decision.conditions.get("reasons", [])
            if credit_decision.conditions
            else []
        )
        decision_detail = DecisionDetail(
            result=credit_decision.decision.value,
            reasons=reasons,
            confidence=credit_decision.confidence,
            decided_at=credit_decision.decided_at,
        )

    # Build offer detail
    offer_detail: Optional[OfferDetail] = None
    if offer:
        emi_schedule = offer.emi_schedule or {}
        interest_rate = float(emi_schedule.get("rate", 0))
        emi_amount = float(emi_schedule.get("emi", 0))
        total_cost = float(offer.total_cost) if offer.total_cost is not None else 0.0
        processing_fee = total_cost * 0.01
        offer_detail = OfferDetail(
            interest_rate=interest_rate,
            emi_amount=emi_amount,
            tenure_months=app.tenure_months,
            processing_fee=processing_fee,
            total_cost=total_cost,
            accepted=offer.accepted,
        )

    return ApplicationDetail(
        id=app.id,
        reference_number=app.reference_number,
        loan_amount=float(app.loan_amount),
        loan_type=app.loan_type.value,
        tenure_months=app.tenure_months,
        status=app.status.value,
        phase_history=phase_history,
        current_phase=current_phase,
        documents=document_items,
        decision=decision_detail,
        offer=offer_detail,
        conversation_id=conversation.id if conversation else None,
    )
