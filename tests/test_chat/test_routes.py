from src.api.routes.chat import router
from src.api.routes.chat import _try_parse_tool_submission


def test_chat_router_has_stream_endpoint():
    paths = [r.path for r in router.routes]
    assert any("stream" in str(p) for p in paths)


def test_chat_router_has_conversations_endpoint():
    paths = [r.path for r in router.routes]
    assert any("conversations" in str(p) for p in paths)


def test_detect_basic_info_form():
    import json
    form_text = json.dumps({
        "tool": "collect_basic_info",
        "full_name": "Raj Kumar",
        "pan_number": "ABCDE1234F",
        "date_of_birth": "1990-03-15",
        "mobile": "9876543210",
        "email": "raj@example.com",
        "employment_type": "salaried",
        "monthly_income": 75000,
        "employer": "TCS",
        "city": "Mumbai",
    })
    parsed = _try_parse_tool_submission(form_text)
    assert parsed is not None
    assert parsed["full_name"] == "Raj Kumar"
    assert parsed["pan_number"] == "ABCDE1234F"


def test_non_form_message_returns_none():
    parsed = _try_parse_tool_submission("I want a loan")
    assert parsed is None


def test_hitl_review_messages():
    """Verify HITL message templates exist."""
    from src.api.routes.hitl import _DECISION_MESSAGES
    assert "approved" in _DECISION_MESSAGES
    assert "denied" in _DECISION_MESSAGES
    assert "status page" in _DECISION_MESSAGES["approved"].lower()
