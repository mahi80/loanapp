"""SSE streaming helpers for Vercel AI SDK UI Message Stream protocol (v1)."""
from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator

import structlog
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from src.graph.graph import build_graph
from src.graph.state import LoanApplicationState

logger = structlog.get_logger()


# -- SSE event formatters (Vercel AI SDK UI Message Stream v1) -----------------

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def format_start_event(message_id: str) -> str:
    return _sse({"type": "start", "messageId": message_id})


def format_text_start(part_id: str) -> str:
    return _sse({"type": "text-start", "id": part_id})


def format_text_delta(part_id: str, delta: str) -> str:
    return _sse({"type": "text-delta", "id": part_id, "delta": delta})


def format_text_end(part_id: str) -> str:
    return _sse({"type": "text-end", "id": part_id})


def format_finish_event(message_id: str) -> str:
    return _sse({"type": "finish", "messageId": message_id})


def format_data_event(data_type: str, data: dict) -> str:
    return _sse({"type": f"data-{data_type}", "id": str(uuid.uuid4())[:8], "data": data})


def format_tool_call_event(tool_name: str, args: dict) -> str:
    """Emit a tool call as a text-embedded JSON marker.
    The frontend chat-interface extracts these markers and renders ToolRenderer components.
    Using custom event types (data-tool-*) or tool-call-start/delta/end breaks the AI SDK parser."""
    marker = json.dumps({"__tool__": tool_name, **args})
    part_id = f"tool_{uuid.uuid4().hex[:8]}"
    events = ""
    events += _sse({"type": "text-start", "id": part_id})
    events += _sse({"type": "text-delta", "id": part_id, "delta": f"<<TOOL:{tool_name}:{marker}>>"})
    events += _sse({"type": "text-end", "id": part_id})
    return events


# -- Stream generator ----------------------------------------------------------

async def stream_langgraph_response(
    state: LoanApplicationState,
    thread_id: str,
    conversation_id: uuid.UUID | None = None,
    application_id: uuid.UUID | None = None,
    is_new_conversation: bool = True,
    resume_value=None,
) -> AsyncGenerator[str, None]:
    from src.graph.checkpointer import get_checkpointer
    from src.db.session import async_session_factory
    from langgraph.types import Command

    checkpointer = get_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    yield format_start_event(message_id)

    # Emit conversation_id so frontend can send it back on subsequent messages
    if conversation_id:
        yield _sse({"type": "text-start", "id": "meta_conv"})
        yield _sse({"type": "text-delta", "id": "meta_conv", "delta": f"<<META:conversation_id:{conversation_id}>>"})
        yield _sse({"type": "text-end", "id": "meta_conv"})

    # Determine input
    if is_new_conversation:
        graph_input = state
    else:
        # Resume after interrupt — pass user's form data / text back
        graph_input = Command(resume=resume_value)

    part_id = f"txt_{uuid.uuid4().hex[:8]}"
    text_started = False
    collected_text: list[str] = []
    collected_tools: list[dict] = []
    collected_phases: list[str] = []

    # -- Track per-node outputs for AgentOutput persistence --
    _BACKGROUND_NODES = {
        "doc_verification", "bureau_pull", "income_verification",
        "risk_assessment", "fraud_detection", "score_aggregation",
        "compliance", "pricing", "decision",
    }
    collected_node_outputs: dict[str, dict] = {}  # node_name → {text, tool_calls}

    try:
        async for chunk in graph.astream(graph_input, config=config, stream_mode=["updates", "custom"]):
            if isinstance(chunk, tuple):
                if len(chunk) == 2:
                    chunk_type, chunk_data = chunk
                else:
                    continue
            elif isinstance(chunk, dict):
                chunk_type = chunk.get("type", "")
                chunk_data = chunk.get("data", {})
            else:
                logger.debug("unknown_chunk_format", chunk_type=type(chunk).__name__)
                continue

            if chunk_type == "updates" and isinstance(chunk_data, dict):
                for node_name, update in chunk_data.items():
                    if not isinstance(update, dict):
                        continue
                    all_messages = update.get("messages", [])
                    for msg in all_messages:
                        msg_type = type(msg).__name__
                        if msg_type == "AIMessage":
                            content = getattr(msg, "content", "")
                            tool_calls = getattr(msg, "tool_calls", [])
                            if content and isinstance(content, str):
                                if not text_started:
                                    yield format_text_start(part_id)
                                    text_started = True
                                yield format_text_delta(part_id, content)
                                collected_text.append(content)
                            for tc in tool_calls:
                                tool_name = tc.get("name", "")
                                tool_args = tc.get("args", {})
                                if tool_name.startswith(("collect_", "upload_", "show_")):
                                    yield format_tool_call_event(tool_name, tool_args)
                                    collected_tools.append({"name": tool_name, "args": tool_args})
                    # Capture background-node outputs for AgentOutput table
                    if node_name in _BACKGROUND_NODES:
                        node_entry = collected_node_outputs.setdefault(
                            node_name, {"text": [], "tool_calls": []}
                        )
                        for msg in all_messages:
                            mt = type(msg).__name__
                            if mt == "AIMessage":
                                c = getattr(msg, "content", "")
                                if c and isinstance(c, str):
                                    node_entry["text"].append(c)
                                for tc in getattr(msg, "tool_calls", []):
                                    node_entry["tool_calls"].append(
                                        {"name": tc.get("name", ""), "args": tc.get("args", {})}
                                    )
                            elif mt == "ToolMessage":
                                c = getattr(msg, "content", "")
                                if c and isinstance(c, str):
                                    node_entry["text"].append(f"[tool_result] {c}")

                    phase = update.get("current_phase")
                    if phase:
                        collected_phases.append(phase)
                        yield format_data_event("status", {"phase": phase, "node": node_name})
            elif chunk_type == "custom":
                yield format_data_event("progress", chunk_data if isinstance(chunk_data, dict) else {})
    except Exception as e:
        logger.error("langgraph_stream_error", error=str(e))
        yield _sse({"type": "error", "error": "An internal error occurred. Please try again."})

    # ── Check for interrupt payloads (from interrupt() calls inside nodes) ──
    try:
        snapshot = await graph.aget_state(config)
        if snapshot and snapshot.tasks:
            for task in snapshot.tasks:
                for intr in task.interrupts:
                    payload = intr.value
                    if not isinstance(payload, dict):
                        continue

                    # Emit progress tracker
                    progress = payload.get("progress")
                    if progress:
                        yield format_tool_call_event("show_progress", progress)
                        collected_tools.append({"name": "show_progress", "args": progress})

                    # Emit text (LLM greeting/response)
                    interrupt_text = payload.get("text")
                    if interrupt_text:
                        if not text_started:
                            yield format_text_start(part_id)
                            text_started = True
                        yield format_text_delta(part_id, interrupt_text)
                        collected_text.append(interrupt_text)

                    # Emit single form tool
                    tool = payload.get("tool")
                    if tool:
                        tool_args = payload.get("tool_args", {})
                        yield format_tool_call_event(tool, tool_args)
                        collected_tools.append({"name": tool, "args": tool_args})

                    # Emit multiple tools (e.g. doc_collection upload widgets)
                    tools_list = payload.get("tools")
                    if tools_list and isinstance(tools_list, list):
                        for t in tools_list:
                            t_name = t.get("name", "")
                            t_args = t.get("args", {})
                            yield format_tool_call_event(t_name, t_args)
                            collected_tools.append({"name": t_name, "args": t_args})
    except Exception as e:
        logger.error("get_interrupt_state_failed", error=str(e))

    if text_started:
        yield format_text_end(part_id)
    yield format_finish_event(message_id)

    # ── Persist DB writes ──
    if (conversation_id or application_id) and (collected_text or collected_tools or collected_phases or collected_node_outputs):
        try:
            async with async_session_factory() as db:
                if conversation_id and (collected_text or collected_tools):
                    from src.db.models import ChatMessage as ChatMessageModel
                    assistant_msg = ChatMessageModel(
                        conversation_id=conversation_id,
                        role="assistant",
                        content="".join(collected_text) if collected_text else None,
                        tool_data={"tool_calls": collected_tools} if collected_tools else None,
                    )
                    db.add(assistant_msg)

                if application_id:
                    from src.db.models import (
                        CreditDecision, DecisionEnum,
                        Application as AppModel, ApplicationStatus,
                        Offer as OfferModel,
                        AgentOutput,
                    )
                    from datetime import datetime, UTC

                    # -- Save per-node AgentOutput records --
                    for node_name, node_data in collected_node_outputs.items():
                        summary_text = "\n".join(node_data["text"]) if node_data["text"] else None
                        output = AgentOutput(
                            application_id=application_id,
                            agent_name=node_name,
                            phase=node_name,
                            output_data={
                                "summary": summary_text,
                                "tool_calls": node_data["tool_calls"] or None,
                            },
                        )
                        db.add(output)

                    for tc in collected_tools:
                        tool_name = tc["name"]
                        tool_args = tc["args"]

                        if tool_name == "show_decision":
                            dec = CreditDecision(
                                application_id=application_id,
                                decision=DecisionEnum(tool_args.get("decision", "escalated").lower()),
                                confidence=tool_args.get("confidence", 0.0),
                                conditions={"reasons": tool_args.get("reasons", [])},
                            )
                            db.add(dec)
                            app_r = await db.execute(select(AppModel).where(AppModel.id == application_id))
                            app_o = app_r.scalar_one_or_none()
                            if app_o:
                                app_o.status = ApplicationStatus.DECIDED

                        elif tool_name == "show_offer":
                            offer = OfferModel(
                                application_id=application_id,
                                emi_schedule={
                                    "emi": tool_args.get("emi_amount", 0),
                                    "rate": tool_args.get("interest_rate", 0),
                                },
                                total_cost=tool_args.get("total_cost", 0),
                            )
                            db.add(offer)

                    if collected_phases:
                        app_result = await db.execute(
                            select(AppModel).where(AppModel.id == application_id)
                        )
                        app_obj = app_result.scalar_one_or_none()
                        if app_obj:
                            from sqlalchemy.orm.attributes import flag_modified
                            history = list(app_obj.phase_history or [])
                            for phase in collected_phases:
                                if not any(p["phase"] == phase for p in history):
                                    history.append({"phase": phase, "completed_at": datetime.now(UTC).isoformat()})
                            app_obj.phase_history = history
                            flag_modified(app_obj, "phase_history")

                await db.commit()
        except Exception as e:
            logger.error("persist_stream_data_failed", error=str(e))


# -- Response factory ----------------------------------------------------------

def create_sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Vercel-AI-UI-Message-Stream": "v1",
        },
    )
