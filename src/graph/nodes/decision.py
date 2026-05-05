from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_decision


async def decision_node(state: LoanApplicationState) -> dict:
    """Apply credit decision rules and render the final APPROVED/DENIED/CONDITIONAL/ESCALATED verdict."""
    llm = get_llm()
    tools = [show_decision]
    system_prompt = build_prompt("decision", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Make the final credit decision.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages, "current_phase": "decision"}
