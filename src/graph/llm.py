"""Shared LLM factory and ReAct agent loop for LangGraph nodes."""
from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.config import get_settings

logger = structlog.get_logger()

MAX_TOOL_ROUNDS = 2


def get_llm() -> ChatAnthropic:
    """Return a ChatAnthropic instance pointed at Azure AI Foundry Claude endpoint."""
    settings = get_settings()
    return ChatAnthropic(
        model=settings.azure_ai_chat_deployment,
        anthropic_api_key=settings.azure_ai_api_key,
        anthropic_api_url=settings.azure_ai_api_base,
        max_tokens=4096,
    )


async def run_agent_node(
    llm: ChatAnthropic,
    tools: list,
    messages: list,
) -> list:
    """Run a ReAct loop: LLM -> execute tools -> LLM -> ... until no more tool calls.

    Returns the full list of new messages produced (AI messages + tool results).
    """
    tool_map = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)
    new_messages = []

    for _ in range(MAX_TOOL_ROUNDS):
        all_msgs = messages + new_messages
        # Claude rejects conversations ending with a plain AIMessage (no tool_calls).
        # If a previous node left an AIMessage at the tail, bridge it with a user message.
        if all_msgs and isinstance(all_msgs[-1], AIMessage) and not getattr(all_msgs[-1], "tool_calls", None):
            bridge = HumanMessage(content="Please proceed.")
            new_messages.append(bridge)
            all_msgs.append(bridge)
        response: AIMessage = await llm_with_tools.ainvoke(all_msgs)
        new_messages.append(response)

        tool_calls = getattr(response, "tool_calls", [])
        if not tool_calls:
            break

        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id = tc.get("id", "")
            func = tool_map.get(tool_name)
            if func:
                try:
                    result = await func.ainvoke(tool_args)
                except Exception as e:
                    result = {"error": str(e)}
                    logger.warning("tool_execution_failed", tool=tool_name, error=str(e))
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            new_messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_id, name=tool_name)
            )

    return new_messages
