from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_offer, generate_emi_schedule_tool


async def offer_generation_node(state: LoanApplicationState) -> dict:
    """Present approved loan offer terms and generate EMI schedule for the customer."""
    llm = get_llm()
    tools = [show_offer, generate_emi_schedule_tool]
    system_prompt = build_prompt("offer_generation", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Generate the loan offer for the customer.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages, "current_phase": "offer_generation"}
