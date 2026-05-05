from src.db.models import (
    Application, ApplicantProfile, Document, BureauReport,
    IncomeVerification, FraudCheck, CreditScore, CreditDecision,
    HITLReview, Offer, Disbursement, AgentOutput, EvolutionHistory,
    Webhook, RateCard, ProductRule, NegativeList, Notification,
    RegulatoryReport, ApiAuditLog,
    ApplicationStatus, DecisionEnum, RiskCategory, EmploymentType,
)


def test_all_19_tables_defined():
    """Verify all 19 spec tables plus ApiAuditLog exist."""
    tables = [
        Application, ApplicantProfile, Document, BureauReport,
        IncomeVerification, FraudCheck, CreditScore, CreditDecision,
        HITLReview, Offer, Disbursement, AgentOutput, EvolutionHistory,
        Webhook, RateCard, ProductRule, NegativeList, Notification,
        RegulatoryReport, ApiAuditLog,
    ]
    assert len(tables) == 20  # 19 spec + ApiAuditLog


def test_application_status_enum():
    assert ApplicationStatus.LEAD.value == "lead"
    assert ApplicationStatus.DISBURSED.value == "disbursed"


def test_decision_enum_has_conditional():
    assert DecisionEnum.CONDITIONAL.value == "conditional"


def test_employment_type_enum():
    assert EmploymentType.SALARIED.value == "salaried"
    assert EmploymentType.SELF_EMPLOYED.value == "self_employed"


def test_application_has_phase_history():
    from src.db.models import Application
    cols = {c.name for c in Application.__table__.columns}
    assert "phase_history" in cols
