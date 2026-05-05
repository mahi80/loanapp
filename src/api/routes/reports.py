from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import CreditDecision, AgentOutput, Application, DecisionEnum
from src.api.models.schemas import KPIReport, AgentReport, AgentPerformance

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/kpis", response_model=KPIReport)
async def get_kpis(period: str = Query("30d"), db: AsyncSession = Depends(get_db)):
    """Dashboard KPIs."""
    total_result = await db.execute(select(func.count(Application.id)))
    total = total_result.scalar() or 0

    approved_result = await db.execute(
        select(func.count(CreditDecision.id)).where(CreditDecision.decision == DecisionEnum.APPROVED)
    )
    approved = approved_result.scalar() or 0

    denied_result = await db.execute(
        select(func.count(CreditDecision.id)).where(CreditDecision.decision == DecisionEnum.DENIED)
    )
    denied = denied_result.scalar() or 0

    approval_rate = approved / total if total > 0 else 0

    return KPIReport(
        default_rate=0.0,  # TODO: Calculate from outcome data
        approval_rate=round(approval_rate, 4),
        avg_processing_time_seconds=0.0,  # TODO: Calculate from timestamps
        thin_file_approval_rate=0.0,  # TODO: Calculate for thin-file applicants
        bias_metrics={},  # TODO: Calculate from demographic data
    )


@router.get("/agents", response_model=AgentReport)
async def get_agent_report(db: AsyncSession = Depends(get_db)):
    """Per-agent performance metrics."""
    result = await db.execute(
        select(
            AgentOutput.agent_name,
            func.avg(AgentOutput.latency_ms).label("avg_latency"),
            func.count(AgentOutput.id).label("total_calls"),
        ).group_by(AgentOutput.agent_name)
    )
    rows = result.all()

    agents = [
        AgentPerformance(
            name=row.agent_name,
            avg_latency_ms=round(row.avg_latency or 0, 2),
            success_rate=1.0,  # TODO: Track failures
            evolution_count=0,  # TODO: Count from evolution_history
            last_evolved=None,
        )
        for row in rows
    ]

    return AgentReport(agents=agents)
