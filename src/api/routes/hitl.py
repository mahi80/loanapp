from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Application, ApplicationStatus, CreditDecision, HITLReview, AgentOutput, DecisionEnum, CreditScore, User, Conversation, ChatMessage
from src.api.models.schemas import (
    HITLQueueResponse, HITLItem, HITLDetailResponse,
    HITLReviewCreate, HITLReviewResponse,
)
from src.auth.middleware import require_role

_DECISION_MESSAGES = {
    "approved": "Great news! Your loan application has been approved. Visit your status page to view the offer details and accept.",
    "denied": "We regret to inform you that your loan application was not approved at this time. Please check your status page for details.",
    "conditional": "Your loan application has been conditionally approved. Please check your status page for the conditions and next steps.",
    "escalated": "Your application requires additional review. We will notify you once a decision has been made.",
}

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])

officer_required = Depends(require_role("officer"))


@router.get("/queue", response_model=HITLQueueResponse)
async def get_hitl_queue(
    status: str = Query("pending"),
    officer_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """List applications pending human review."""
    from sqlalchemy.orm import selectinload
    query = (
        select(Application)
        .join(CreditDecision, CreditDecision.application_id == Application.id)
        .outerjoin(HITLReview, HITLReview.application_id == Application.id)
        .where(
            CreditDecision.decision == DecisionEnum.ESCALATED,
            HITLReview.id.is_(None),  # Exclude already-reviewed
        )
        .options(
            selectinload(Application.decision),
            selectinload(Application.credit_score),
        )
    )
    result = await db.execute(query)
    applications = result.scalars().all()

    items = []
    for app in applications:
        decision = app.decision
        credit_score = app.credit_score

        # Derive risk flags
        risk_flags: list[str] = []
        if credit_score:
            if credit_score.dti_ratio is not None and credit_score.dti_ratio > 0.50:
                risk_flags.append("Borderline DTI")
            if credit_score.composite_score is not None and credit_score.composite_score < 600:
                risk_flags.append("Low score")
        if float(app.loan_amount) > 1_000_000:
            risk_flags.append("High amt")

        waiting_since = decision.decided_at.isoformat() if decision and decision.decided_at else None

        items.append(HITLItem(
            application_id=app.id,
            applicant_name=app.applicant_name,
            reference_number=app.reference_number or "",
            loan_amount=float(app.loan_amount),
            composite_score=credit_score.composite_score if credit_score else None,
            risk_flags=risk_flags,
            waiting_since=waiting_since,
            escalation_reason="Borderline risk score - requires human review",
            priority="medium",
            agent_recommendation=decision.decision if decision else DecisionEnum.ESCALATED,
        ))

    return HITLQueueResponse(items=items)


@router.get("/{application_id}", response_model=HITLDetailResponse)
async def get_hitl_detail(application_id: uuid.UUID, db: AsyncSession = Depends(get_db), _officer: User = officer_required):
    """Get full context for human review."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    outputs_result = await db.execute(
        select(AgentOutput).where(AgentOutput.application_id == application_id)
    )
    outputs = outputs_result.scalars().all()

    decision_result = await db.execute(
        select(CreditDecision).where(CreditDecision.application_id == application_id)
    )
    decision = decision_result.scalar_one_or_none()

    return HITLDetailResponse(
        application_id=application_id,
        full_application_data={
            "applicant_name": app.applicant_name,
            "loan_amount": app.loan_amount,
            "loan_type": app.loan_type.value,
            "status": app.status.value,
        },
        agent_outputs=[{"agent": o.agent_name, "output": o.output_data} for o in outputs],
        recommended_decision=decision.decision if decision else DecisionEnum.ESCALATED,
        risk_flags=decision.conditions.get("risk_flags", []) if decision and decision.conditions else [],
    )


@router.post("/{application_id}/review", response_model=HITLReviewResponse)
async def submit_review(
    application_id: uuid.UUID,
    review: HITLReviewCreate,
    db: AsyncSession = Depends(get_db),
    officer: User = officer_required,
):
    """Submit officer's decision. Feeds back into evolution loop."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    hitl_review = HITLReview(
        application_id=application_id,
        officer_id=str(officer.id),
        officer_decision=review.decision,
        notes=review.officer_notes,
        override_reason=review.override_reason,
    )
    db.add(hitl_review)

    # Update application status based on officer decision
    if review.decision in (DecisionEnum.APPROVED, DecisionEnum.CONDITIONAL, DecisionEnum.DENIED):
        app.status = ApplicationStatus.DECIDED

    # Update existing CreditDecision (unique constraint on application_id)
    existing_dec_result = await db.execute(
        select(CreditDecision).where(CreditDecision.application_id == application_id)
    )
    existing_dec = existing_dec_result.scalar_one_or_none()
    if existing_dec:
        existing_dec.decision = review.decision
        existing_dec.confidence = 1.0
        existing_dec.rationale = review.officer_notes
        existing_dec.conditions = {"reasons": [review.override_reason]} if review.override_reason else None
    else:
        dec = CreditDecision(
            application_id=application_id,
            decision=review.decision,
            confidence=1.0,
            rationale=review.officer_notes,
            conditions={"reasons": [review.override_reason]} if review.override_reason else None,
        )
        db.add(dec)

    # Inject assistant message into customer conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.application_id == application_id)
    )
    conv = conv_result.scalar_one_or_none()
    if conv:
        msg_text = _DECISION_MESSAGES.get(review.decision.value, _DECISION_MESSAGES["escalated"])
        chat_msg = ChatMessage(
            conversation_id=conv.id,
            role="assistant",
            content=msg_text,
        )
        db.add(chat_msg)

    # TODO: Feed back into evolution loop for learning

    return HITLReviewResponse(status="reviewed", final_decision=review.decision)
