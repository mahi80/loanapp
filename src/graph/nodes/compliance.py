from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import check_bias_tool


async def compliance_node(state: LoanApplicationState) -> dict:
    """Validate against RBI guidelines, fair lending rules, and KYC requirements."""
    llm = get_llm()
    tools = [check_bias_tool]
    system_prompt = build_prompt("compliance", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Run compliance checks.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages}
