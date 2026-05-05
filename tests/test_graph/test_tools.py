from src.graph.tools import (
    check_eligibility_tool, calculate_dti_tool, calculate_risk_score_tool,
    score_four_cs_tool, lookup_rate_tool, generate_emi_schedule_tool,
    check_negative_list_tool, aggregate_scores_tool,
    calculate_volatility_tool, scan_hidden_debts_tool, check_bias_tool,
    CUSTOMER_FACING_TOOLS, BACKEND_TOOLS,
)


def test_eligibility_tool_callable():
    result = check_eligibility_tool.invoke({"age": 30, "monthly_income": 50000, "city": "Mumbai", "loan_amount": 500000})
    assert result["eligible"] is True


def test_eligibility_tool_rejects_underage():
    result = check_eligibility_tool.invoke({"age": 18, "monthly_income": 50000, "city": "Mumbai", "loan_amount": 500000})
    assert result["eligible"] is False


def test_dti_tool_callable():
    result = calculate_dti_tool.invoke({"monthly_income": 100000, "existing_emis": 20000, "proposed_emi": 15000})
    assert "dti_ratio" in result
    assert result["dti_ratio"] > 0


def test_customer_facing_tools_list():
    assert len(CUSTOMER_FACING_TOOLS) >= 3


def test_backend_tools_list():
    assert len(BACKEND_TOOLS) >= 5
