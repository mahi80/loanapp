from src.graph.state import LoanApplicationState


def test_state_has_required_keys():
    state = LoanApplicationState(
        messages=[], user_id="u1", application_id="", reference_number="",
        current_phase="intake", conversation_complete=False, needs_human_review=False,
    )
    assert state["user_id"] == "u1"
    assert state["current_phase"] == "intake"


def test_state_has_document_tracking():
    state = LoanApplicationState(
        messages=[], user_id="u1", application_id="", reference_number="",
        current_phase="intake", conversation_complete=False, needs_human_review=False,
        documents_uploaded={}, documents_required=[], documents_pending=[],
    )
    assert state["documents_uploaded"] == {}


def test_state_has_scoring_fields():
    state = LoanApplicationState(
        messages=[], user_id="u1", application_id="", reference_number="",
        current_phase="intake", conversation_complete=False, needs_human_review=False,
        composite_score=0, risk_category="",
    )
    assert state["composite_score"] == 0
