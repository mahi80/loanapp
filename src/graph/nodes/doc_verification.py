from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from src.graph.llm import get_llm, run_agent_node
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_verification, show_progress, extract_document_tool, cross_validate_documents


async def doc_verification_node(state: LoanApplicationState) -> dict:
    """Extract and cross-validate data from uploaded documents."""
    llm = get_llm()
    tools = [show_verification, show_progress, extract_document_tool, cross_validate_documents]
    system_prompt = build_prompt("doc_verification", state)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content="Verify the uploaded documents.")]
    new_messages = await run_agent_node(llm, tools, messages)
    return {"messages": new_messages, "current_phase": "doc_verification"}
