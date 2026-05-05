from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


async def bureau_pull_node(state: LoanApplicationState) -> dict:
    """Pull and consolidate credit bureau reports from CIBIL, Experian, CRIF, and Equifax."""
    llm = get_llm()
    system_prompt = build_prompt("bureau_pull", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Pull credit bureau reports.")]
    new_messages = await run_agent_node(llm, [], messages)
    return {"messages": new_messages}
