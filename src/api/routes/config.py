from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import RateCard, ProductRule, LoanType, RuleType, User
from src.auth.middleware import require_role

router = APIRouter(prefix="/api/v1/config", tags=["config"])

officer_required = Depends(require_role("officer"))

_DEFAULT_DOC_CONFIG = {
    "groups": [
        {
            "name": "Identity",
            "documents": [
                {"type": "pan_card", "label": "PAN Card", "required": True},
                {"type": "aadhaar", "label": "Aadhaar", "required": True},
            ],
        },
        {
            "name": "Income",
            "documents": [
                {"type": "payslip", "label": "Latest 3 Payslips", "required": True},
                {"type": "bank_statement", "label": "6-Month Bank Statement", "required": True},
            ],
        },
    ]
}


class RateCardUpdate(BaseModel):
    interest_rate: float | None = None
    processing_fee_pct: float | None = None
    insurance_pct: float | None = None


class ProductRuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_config: dict | None = None
    active: bool | None = None


class DocumentRequirementsUpdate(BaseModel):
    loan_type: str
    config: dict


@router.get("/rate-cards")
async def get_rate_cards(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Current rate card configuration."""
    result = await db.execute(select(RateCard).where(RateCard.active == True))
    cards = result.scalars().all()
    return [{"id": str(c.id), "product_type": c.product_type.value, "risk_category": c.risk_category.value,
             "interest_rate": c.interest_rate, "processing_fee_pct": c.processing_fee_pct,
             "insurance_pct": c.insurance_pct, "min_score": c.min_score, "max_score": c.max_score} for c in cards]


@router.put("/rate-cards/{card_id}")
async def update_rate_card(
    card_id: uuid.UUID,
    updates: RateCardUpdate,
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Update rate card (admin only)."""
    result = await db.execute(select(RateCard).where(RateCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Rate card not found")

    if updates.interest_rate is not None:
        card.interest_rate = updates.interest_rate
    if updates.processing_fee_pct is not None:
        card.processing_fee_pct = updates.processing_fee_pct
    if updates.insurance_pct is not None:
        card.insurance_pct = updates.insurance_pct

    return {
        "id": str(card.id), "product_type": card.product_type.value,
        "risk_category": card.risk_category.value,
        "interest_rate": card.interest_rate, "processing_fee_pct": card.processing_fee_pct,
        "insurance_pct": card.insurance_pct, "min_score": card.min_score, "max_score": card.max_score,
    }


@router.get("/product-rules")
async def get_product_rules(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Product eligibility rules."""
    result = await db.execute(select(ProductRule).where(ProductRule.active == True))
    rules = result.scalars().all()
    return [{"id": str(r.id), "product_type": r.product_type.value, "rule_name": r.rule_name,
             "rule_type": r.rule_type.value, "rule_config": r.rule_config} for r in rules]


@router.put("/product-rules/{rule_id}")
async def update_product_rule(
    rule_id: uuid.UUID,
    updates: ProductRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Update product rules (admin only)."""
    result = await db.execute(select(ProductRule).where(ProductRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if updates.rule_name is not None:
        rule.rule_name = updates.rule_name
    if updates.rule_config is not None:
        rule.rule_config = updates.rule_config
    if updates.active is not None:
        rule.active = updates.active

    return {"status": "updated"}


@router.get("/document-requirements")
async def get_document_requirements(
    loan_type: str = Query("personal"),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Get document requirements config for a loan type."""
    # Validate loan_type
    try:
        lt = LoanType(loan_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid loan_type: {loan_type}")

    result = await db.execute(
        select(ProductRule).where(
            and_(
                ProductRule.rule_name == "document_requirements",
                ProductRule.product_type == lt,
                ProductRule.active == True,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if rule:
        return rule.rule_config
    else:
        return _DEFAULT_DOC_CONFIG


@router.post("/document-requirements")
async def upsert_document_requirements(
    body: DocumentRequirementsUpdate,
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Upsert document requirements config for a loan type."""
    try:
        lt = LoanType(body.loan_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid loan_type: {body.loan_type}")

    result = await db.execute(
        select(ProductRule).where(
            and_(
                ProductRule.rule_name == "document_requirements",
                ProductRule.product_type == lt,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if rule:
        rule.rule_config = body.config
        rule.active = True
    else:
        rule = ProductRule(
            product_type=lt,
            rule_name="document_requirements",
            rule_type=RuleType.POLICY,
            rule_config=body.config,
            active=True,
        )
        db.add(rule)

    await db.flush()
    return {"status": "saved", "loan_type": body.loan_type}
