from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import CreditDecision

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/decisions")
async def get_decision_audit(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Query audit trail of all decisions."""
    result = await db.execute(
        select(CreditDecision)
        .order_by(CreditDecision.decided_at.desc())
        .offset(offset)
        .limit(limit)
    )
    decisions = result.scalars().all()

    return {
        "decisions": [
            {
                "application_id": str(d.application_id),
                "decision": d.decision.value,
                "confidence": d.confidence,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
                "rationale": d.rationale,
            }
            for d in decisions
        ]
    }
