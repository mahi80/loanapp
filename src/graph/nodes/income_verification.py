from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import calculate_volatility_tool, scan_hidden_debts_tool


async def income_verification_node(state: LoanApplicationState) -> dict:
    """Verify income from bank statements, payslips, and employer data."""
    llm = get_llm()
    tools = [calculate_volatility_tool, scan_hidden_debts_tool]
    system_prompt = build_prompt("income_verification", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Verify the applicant's income.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages}
