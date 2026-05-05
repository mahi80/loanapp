from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Application, ApplicantProfile, ApplicationStatus, Document, EmploymentType
from src.api.models.schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationStatusResponse,
    DecisionResponse, TimelineResponse, AgentStageInfo,
)

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(payload: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    """Submit a new loan application. Triggers the EvoAgentX workflow."""
    application = Application(
        applicant_name=payload.applicant_info.name,
        pan_number=payload.applicant_info.pan_number,
        mobile=payload.applicant_info.mobile,
        loan_amount=payload.loan_details.amount,
        loan_type=payload.loan_details.loan_type,
        tenure_months=payload.loan_details.tenure_months,
        employment_type=payload.applicant_info.employment_type,
        status=ApplicationStatus.LEAD,
    )
    db.add(application)
    await db.flush()

    profile = ApplicantProfile(
        application_id=application.id,
        income=payload.applicant_info.income,
        employer=payload.applicant_info.employer,
        employment_type=payload.applicant_info.employment_type,
        address=payload.applicant_info.address,
        dob=payload.applicant_info.dob,
        mobile=payload.applicant_info.mobile,
        email=payload.applicant_info.email,
        city=payload.applicant_info.city,
        state=payload.applicant_info.state,
    )
    db.add(profile)

    return ApplicationResponse(
        application_id=application.id,
        status=application.status,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.get("/{application_id}", response_model=ApplicationStatusResponse)
async def get_application(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get application status and processing stage."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationStatusResponse(
        application_id=app.id,
        status=app.status,
        created_at=app.created_at,
        updated_at=app.updated_at,
        current_stage=app.status.value,
    )


@router.get("/{application_id}/decision", response_model=DecisionResponse)
async def get_decision(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get the final credit decision with score and explanations."""
    from src.db.models import CreditDecision

    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(select(CreditDecision).where(CreditDecision.application_id == application_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not yet available")

    reasons = decision.conditions.get("reasons", []) if decision.conditions else []

    return DecisionResponse(
        application_id=application_id,
        decision=decision.decision,
        confidence=decision.confidence,
        reasons=reasons,
    )


@router.get("/{application_id}/timeline", response_model=TimelineResponse)
async def get_timeline(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed timeline of each agent's processing."""
    from src.db.models import AgentOutput

    result = await db.execute(
        select(AgentOutput)
        .where(AgentOutput.application_id == application_id)
        .order_by(AgentOutput.created_at)
    )
    outputs = result.scalars().all()

    stages = [
        AgentStageInfo(
            agent=o.agent_name,
            status="completed",
            started_at=o.created_at,
            completed_at=o.created_at,
            output_summary=o.output_data,
        )
        for o in outputs
    ]

    return TimelineResponse(application_id=application_id, stages=stages)


@router.delete("/{application_id}")
async def cancel_application(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Cancel a pending application."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.status in (ApplicationStatus.DECIDED, ApplicationStatus.DISBURSED):
        raise HTTPException(status_code=400, detail="Cannot cancel a finalized application")

    app.status = ApplicationStatus.CANCELLED
    return {"status": "cancelled"}


@router.get("/{application_id}/documents/checklist")
async def get_document_checklist(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Document checklist with status per required doc."""
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    profile_result = await db.execute(
        select(ApplicantProfile).where(ApplicantProfile.application_id == application_id)
    )
    profile = profile_result.scalar_one_or_none()

    docs_result = await db.execute(
        select(Document).where(Document.application_id == application_id)
    )
    uploaded_docs = {d.type.value for d in docs_result.scalars().all()}

    required = ["pan_card", "aadhaar", "bank_statement", "selfie"]
    if profile and profile.employment_type == EmploymentType.SALARIED:
        required.extend(["payslip", "form_16"])
    elif profile and profile.employment_type == EmploymentType.SELF_EMPLOYED:
        required.extend(["itr", "gst_certificate"])

    checklist = [{"document_type": r, "required": True, "uploaded": r in uploaded_docs} for r in required]

    return {"application_id": str(application_id), "checklist": checklist,
            "complete": all(item["uploaded"] for item in checklist)}
