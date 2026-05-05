from src.graph.prompts.builder import build_prompt


def test_intake_prompt_contains_role():
    prompt = build_prompt("intake", {})
    assert "loan" in prompt.lower()


def test_intake_prompt_with_applicant_context():
    state = {"applicant_name": "Raj Kumar", "employment_type": "salaried"}
    prompt = build_prompt("intake", state)
    assert "Raj Kumar" in prompt
    assert "salaried" in prompt


def test_doc_collection_prompt_includes_required_docs():
    state = {"employment_type": "salaried", "documents_required": ["pan_card", "aadhaar", "payslip"]}
    prompt = build_prompt("doc_collection", state)
    assert "pan_card" in prompt


def test_unknown_phase_returns_generic():
    prompt = build_prompt("unknown_phase", {})
    assert len(prompt) > 0


def test_risk_assessment_prompt_includes_bureau():
    state = {"bureau_reports": {"cibil": {"score": 750}}}
    prompt = build_prompt("risk_assessment", state)
    assert "750" in prompt or "bureau" in prompt.lower()
