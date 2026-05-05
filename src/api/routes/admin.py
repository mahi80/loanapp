from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import (
    User, Application, ApplicationStatus,
    CreditDecision, DecisionEnum, CreditScore, HITLReview,
)
from src.auth.middleware import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

officer_required = Depends(require_role("officer"))


@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Dashboard KPI stats."""
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(weeks=1)
    four_weeks_ago = now - timedelta(weeks=4)

    # Total application count
    total_result = await db.execute(select(func.count(Application.id)))
    total_applications = total_result.scalar() or 0

    # Applications from last week (for weekly change)
    weekly_result = await db.execute(
        select(func.count(Application.id)).where(Application.created_at >= one_week_ago)
    )
    weekly_new = weekly_result.scalar() or 0

    # Applications from 4 weeks ago to 3 weeks ago (comparison period for weekly)
    two_weeks_ago = now - timedelta(weeks=2)
    prev_week_result = await db.execute(
        select(func.count(Application.id)).where(
            Application.created_at >= two_weeks_ago,
            Application.created_at < one_week_ago,
        )
    )
    prev_week_count = prev_week_result.scalar() or 0
    weekly_change_pct = round(
        ((weekly_new - prev_week_count) / prev_week_count * 100) if prev_week_count else 0.0, 1
    )

    # Monthly change
    monthly_result = await db.execute(
        select(func.count(Application.id)).where(Application.created_at >= four_weeks_ago)
    )
    monthly_new = monthly_result.scalar() or 0
    eight_weeks_ago = now - timedelta(weeks=8)
    prev_month_result = await db.execute(
        select(func.count(Application.id)).where(
            Application.created_at >= eight_weeks_ago,
            Application.created_at < four_weeks_ago,
        )
    )
    prev_month_count = prev_month_result.scalar() or 0
    monthly_change_pct = round(
        ((monthly_new - prev_month_count) / prev_month_count * 100) if prev_month_count else 0.0, 1
    )

    # Decision breakdown
    breakdown_result = await db.execute(
        select(CreditDecision.decision, func.count(CreditDecision.id))
        .group_by(CreditDecision.decision)
    )
    breakdown_rows = breakdown_result.all()
    decision_breakdown = {d.value: 0 for d in DecisionEnum}
    for decision, count in breakdown_rows:
        decision_breakdown[decision.value] = count

    # AI confidence avg
    confidence_result = await db.execute(
        select(func.avg(CreditScore.confidence))
    )
    avg_conf = confidence_result.scalar()
    ai_confidence_pct = round((avg_conf or 0.0) * 100, 1)

    # Override rate: HITLReview count / CreditDecision count
    hitl_count_result = await db.execute(select(func.count(HITLReview.id)))
    hitl_count = hitl_count_result.scalar() or 0
    total_decisions_result = await db.execute(select(func.count(CreditDecision.id)))
    total_decisions = total_decisions_result.scalar() or 0
    override_rate_pct = round((hitl_count / total_decisions * 100) if total_decisions else 0.0, 1)

    # Avg processing hours: avg time between Application.created_at and CreditDecision.decided_at
    processing_result = await db.execute(
        select(Application.created_at, CreditDecision.decided_at)
        .join(CreditDecision, CreditDecision.application_id == Application.id)
    )
    processing_rows = processing_result.all()
    if processing_rows:
        diffs_hours = []
        for created_at, decided_at in processing_rows:
            if created_at and decided_at:
                # Make both tz-aware if needed
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if decided_at.tzinfo is None:
                    decided_at = decided_at.replace(tzinfo=timezone.utc)
                diff = (decided_at - created_at).total_seconds() / 3600
                diffs_hours.append(diff)
        avg_processing_hours = round(sum(diffs_hours) / len(diffs_hours), 1) if diffs_hours else 0.0
    else:
        avg_processing_hours = 0.0

    # Processing change: compare avg for last week vs prior week
    # (simplified: just return 0 if not enough data)
    processing_change_pct = 0.0

    # Pending review: escalated decisions with no HITLReview
    pending_result = await db.execute(
        select(Application, CreditDecision)
        .join(CreditDecision, CreditDecision.application_id == Application.id)
        .outerjoin(HITLReview, HITLReview.application_id == Application.id)
        .where(
            CreditDecision.decision == DecisionEnum.ESCALATED,
            HITLReview.id.is_(None),
        )
    )
    pending_rows = pending_result.all()
    pending_review_count = len(pending_rows)

    # Oldest pending (minutes since escalation decision)
    oldest_pending_minutes = 0
    if pending_rows:
        oldest_dt = None
        for _app, decision in pending_rows:
            decided_at = decision.decided_at
            if decided_at is not None:
                if decided_at.tzinfo is None:
                    decided_at = decided_at.replace(tzinfo=timezone.utc)
                if oldest_dt is None or decided_at < oldest_dt:
                    oldest_dt = decided_at
        if oldest_dt:
            oldest_pending_minutes = int((now - oldest_dt).total_seconds() / 60)

    return {
        "total_applications": total_applications,
        "weekly_change_pct": weekly_change_pct,
        "monthly_change_pct": monthly_change_pct,
        "decision_breakdown": decision_breakdown,
        "ai_confidence_pct": ai_confidence_pct,
        "override_rate_pct": override_rate_pct,
        "avg_processing_hours": avg_processing_hours,
        "processing_change_pct": processing_change_pct,
        "pending_review_count": pending_review_count,
        "oldest_pending_minutes": oldest_pending_minutes,
    }


@router.get("/recent-applications")
async def get_recent_applications(
    limit: int = Query(4, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Recent applications with decision info."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.decision))
        .order_by(Application.created_at.desc())
        .limit(limit)
    )
    apps = result.scalars().all()

    return [
        {
            "id": str(app.id),
            "applicant_name": app.applicant_name,
            "reference_number": app.reference_number,
            "loan_type": app.loan_type.value,
            "loan_amount": float(app.loan_amount),
            "status": app.status.value,
            "decision": app.decision.decision.value if app.decision else None,
            "created_at": app.created_at.isoformat(),
        }
        for app in apps
    ]


@router.get("/analytics/trends")
async def get_trends(
    weeks: int = Query(8, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Weekly decision counts for trend chart."""
    now = datetime.now(timezone.utc)

    result = []
    for i in range(weeks - 1, -1, -1):
        week_start = now - timedelta(weeks=i + 1)
        week_end = now - timedelta(weeks=i)

        # ISO week label
        iso_year, iso_week, _ = week_start.isocalendar()
        week_label = f"{iso_year}-W{iso_week:02d}"

        counts = {d.value: 0 for d in DecisionEnum}
        dec_result = await db.execute(
            select(CreditDecision.decision, func.count(CreditDecision.id))
            .where(
                CreditDecision.decided_at >= week_start,
                CreditDecision.decided_at < week_end,
            )
            .group_by(CreditDecision.decision)
        )
        for decision, count in dec_result.all():
            counts[decision.value] = count

        result.append({"week": week_label, **counts})

    return {"weeks": result}


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Score bucket distribution from CreditScore.composite_score."""
    buckets = [
        {"range": "700-900", "category": "low", "min": 700, "max": 900},
        {"range": "600-699", "category": "medium", "min": 600, "max": 699},
        {"range": "450-599", "category": "high", "min": 450, "max": 599},
        {"range": "300-449", "category": "very_high", "min": 300, "max": 449},
    ]

    result_buckets = []
    for bucket in buckets:
        count_result = await db.execute(
            select(func.count(CreditScore.id)).where(
                CreditScore.composite_score >= bucket["min"],
                CreditScore.composite_score <= bucket["max"],
            )
        )
        count = count_result.scalar() or 0
        result_buckets.append({
            "range": bucket["range"],
            "category": bucket["category"],
            "count": count,
        })

    return {"buckets": result_buckets}


@router.get("/analytics/audit-trail")
async def get_audit_trail(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Audit trail: AI decisions with optional officer overrides."""
    result = await db.execute(
        select(CreditDecision, Application, HITLReview)
        .join(Application, Application.id == CreditDecision.application_id)
        .outerjoin(HITLReview, HITLReview.application_id == CreditDecision.application_id)
        .order_by(CreditDecision.decided_at.desc())
        .limit(limit)
    )
    rows = result.all()

    items = []
    for decision, app, review in rows:
        officer_decision = review.officer_decision.value if review else None
        is_override = (
            review is not None and review.officer_decision != decision.decision
        )
        items.append({
            "application_id": str(app.id),
            "applicant_name": app.applicant_name,
            "ai_decision": decision.decision.value,
            "officer_decision": officer_decision,
            "is_override": is_override,
            "confidence": decision.confidence,
            "notes": review.notes if review else None,
            "decided_at": decision.decided_at.isoformat(),
        })

    return items
