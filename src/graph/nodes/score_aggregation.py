from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import aggregate_scores_tool


async def score_aggregation_node(state: LoanApplicationState) -> dict:
    """Combine 4C scores, income stability, and fraud flags into a composite credit score."""
    llm = get_llm()
    tools = [aggregate_scores_tool]
    system_prompt = build_prompt("score_aggregation", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Aggregate scores and determine risk category.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages, "current_phase": "score_aggregation"}
