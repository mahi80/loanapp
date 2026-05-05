from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


async def human_review_node(state: LoanApplicationState) -> dict:
    """Escalate application to human credit officer and notify the customer."""
    llm = get_llm()
    system_prompt = build_prompt("human_review", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Inform the customer about the escalation.")]
    new_messages = await run_agent_node(llm, [], messages)
    return {
        "messages": new_messages,
        "current_phase": "human_review",
        "needs_human_review": True,
        "conversation_complete": True,
    }
