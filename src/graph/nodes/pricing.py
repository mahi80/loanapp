from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import lookup_rate_tool, estimate_emi_tool, generate_emi_schedule_tool


async def pricing_node(state: LoanApplicationState) -> dict:
    """Look up interest rate, calculate processing fee, EMI, and total cost of credit."""
    llm = get_llm()
    tools = [lookup_rate_tool, estimate_emi_tool, generate_emi_schedule_tool]
    system_prompt = build_prompt("pricing", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Calculate loan pricing and EMI.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages}
