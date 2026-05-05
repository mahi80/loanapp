from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


async def fraud_detection_node(state: LoanApplicationState) -> dict:
    """Analyze identity fraud, document tampering, and calculate fraud risk score."""
    llm = get_llm()
    system_prompt = build_prompt("fraud_detection", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Run fraud detection checks.")]
    new_messages = await run_agent_node(llm, [], messages)
    return {"messages": new_messages, "current_phase": "fraud_detection"}
