from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import (
    score_four_cs_tool,
    calculate_dti_tool,
    calculate_risk_score_tool,
    calculate_volatility_tool,
    scan_hidden_debts_tool,
)


async def risk_assessment_node(state: LoanApplicationState) -> dict:
    """Evaluate credit risk using the 4Cs framework, DTI ratio, and income stability."""
    llm = get_llm()
    tools = [
        score_four_cs_tool,
        calculate_dti_tool,
        calculate_risk_score_tool,
        calculate_volatility_tool,
        scan_hidden_debts_tool,
    ]
    system_prompt = build_prompt("risk_assessment", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Assess credit risk using the 4Cs framework.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages, "current_phase": "risk_assessment"}
