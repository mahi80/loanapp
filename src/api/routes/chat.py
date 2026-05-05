from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage

from src.db.session import get_db
from src.db.models import (
    User, Conversation, ChatMessage,
    Application, ApplicantProfile, ApplicationStatus, LoanType, EmploymentType, Document,
)
from src.auth.middleware import get_current_user
from src.chat.stream import stream_langgraph_response, create_sse_response
from src.graph.state import LoanApplicationState

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class UIMessage(BaseModel):
    """A single message from the Vercel AI SDK UIMessage format."""
    role: str
    content: str | None = None
    parts: list[dict] | None = None
    id: str | None = None


class ChatStreamRequest(BaseModel):
    """Accept both Vercel AI SDK format and legacy format."""
    # Vercel AI SDK sends { messages: [...] }
    messages: list[UIMessage] | None = None
    # Legacy format
    message: str | None = None
    conversation_id: str | None = None
    form_data: dict | None = None
    # AI SDK may send an id for the chat
    id: str | None = None


def _extract_user_message(req: ChatStreamRequest) -> str:
    """Extract the latest user message text from the request."""
    if req.messages:
        # Find the last user message from the AI SDK messages array
        for msg in reversed(req.messages):
            if msg.role == "user":
                # The SDK sends content as text; parts may also have text
                if msg.content:
                    return msg.content
                if msg.parts:
                    texts = [p.get("text", "") for p in msg.parts if p.get("type") == "text"]
                    if texts:
                        return " ".join(texts)
        return ""
    return req.message or ""


_TOOL_SUBMISSIONS = frozenset({
    "collect_basic_info",
    "collect_loan_details",
    "upload_document",          # legacy single-doc resume
    "documents_submitted",      # batched upload resume
})


def _try_parse_tool_submission(user_text: str) -> dict | None:
    """Detect if user_text is a tool form submission. Returns parsed form data or None."""
    if not user_text.strip().startswith("{"):
        return None
    try:
        data = json.loads(user_text)
        if data.get("tool") in _TOOL_SUBMISSIONS:
            return data
        return None
    except (json.JSONDecodeError, AttributeError):
        return None


@router.post("/stream")
async def chat_stream(
    req: ChatStreamRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat response using LangGraph. Returns SSE events compatible with Vercel AI SDK."""
    user_text = _extract_user_message(req)
    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No message content provided")

    # Resolve or create conversation
    # Note: AI SDK sends an `id` like "chat_abc123" which is NOT a conversation UUID.
    # Only use req.id if it's a valid UUID; otherwise treat as new conversation.
    conv_id = req.conversation_id
    if not conv_id and req.id:
        try:
            uuid.UUID(req.id)  # Validate it's a real UUID
            conv_id = req.id
        except ValueError:
            pass  # SDK-generated id like "chat_xxx" — ignore, create new conversation

    is_new = False
    if conv_id:
        try:
            parsed_id = uuid.UUID(conv_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation_id format")
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == parsed_id,
                Conversation.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=user.id,
            current_phase="intake",
            langgraph_thread_id=f"thread_{uuid.uuid4().hex[:16]}",
        )
        db.add(conversation)
        await db.flush()
        is_new = True

    # Persist user message
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=user_text,
        tool_data=req.form_data,
    )
    db.add(user_msg)
    await db.flush()

    # Detect form submissions and handle accordingly
    form_data = _try_parse_tool_submission(user_text)

    # Basic info form → create Application
    if form_data and form_data.get("tool") == "collect_basic_info" and not conversation.application_id:
        ref = f"LN-{uuid.uuid4().hex[:8].upper()}"
        emp_type = None
        if form_data.get("employment_type") in ("salaried", "self_employed"):
            emp_type = EmploymentType(form_data["employment_type"])

        application = Application(
            applicant_name=form_data.get("full_name", ""),
            pan_number=form_data.get("pan_number", ""),
            mobile=form_data.get("mobile"),
            loan_amount=0,
            loan_type=LoanType.PERSONAL,
            employment_type=emp_type,
            status=ApplicationStatus.LEAD,
            user_id=user.id,
            reference_number=ref,
            phase_history=[{"phase": "intake", "completed_at": datetime.now(UTC).isoformat()}],
        )
        db.add(application)
        await db.flush()

        profile = ApplicantProfile(
            application_id=application.id,
            income=form_data.get("monthly_income"),
            employer=form_data.get("employer"),
            employment_type=emp_type,
            city=form_data.get("city"),
            email=form_data.get("email"),
            mobile=form_data.get("mobile"),
        )
        db.add(profile)

        conversation.application_id = application.id
        await db.flush()

        # Link orphaned documents uploaded by this user
        orphan_result = await db.execute(
            select(Document).where(
                Document.application_id.is_(None),
                Document.uploaded_by == user.id,
            )
        )
        for doc in orphan_result.scalars().all():
            doc.application_id = application.id

    # Loan details form → update Application with loan type, amount, tenure
    if form_data and form_data.get("tool") == "collect_loan_details" and conversation.application_id:
        app_result = await db.execute(
            select(Application).where(Application.id == conversation.application_id)
        )
        app_obj = app_result.scalar_one_or_none()
        if app_obj:
            loan_type_str = form_data.get("loan_type", "personal")
            if loan_type_str in ("personal", "home", "auto", "business"):
                app_obj.loan_type = LoanType(loan_type_str)
            if form_data.get("loan_amount"):
                app_obj.loan_amount = form_data["loan_amount"]
            if form_data.get("tenure"):
                app_obj.tenure_months = form_data["tenure"]

    # Commit all DB writes so the stream's separate session can see them
    await db.commit()

    # Build resume value for interrupted graphs
    # If this is a form submission resuming an interrupt, pass the form data as resume value
    resume_value = None
    if not is_new:
        resume_value = form_data if form_data else user_text

    # For new conversations, build full initial state from DB history
    if is_new:
        latest_content = user_text
        latest_message = HumanMessage(content=latest_content)

        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.created_at)
        )
        history = history_result.scalars().all()

        messages = []
        for msg in history:
            if msg.role == "user":
                content = msg.content or ""
                if msg.tool_data:
                    content += f"\n[Form Data]: {json.dumps(msg.tool_data)}"
                messages.append(HumanMessage(content=content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content or ""))

        state = LoanApplicationState(
            messages=messages,
            user_id=str(user.id),
            application_id=str(conversation.application_id or ""),
            reference_number="",
            current_phase=conversation.current_phase or "intake",
            conversation_complete=False,
            needs_human_review=False,
        )
    else:
        state = LoanApplicationState(messages=[], user_id=str(user.id))

    generator = stream_langgraph_response(
        state=state,
        thread_id=conversation.langgraph_thread_id or f"thread_{conversation.id}",
        conversation_id=conversation.id,
        application_id=conversation.application_id,
        is_new_conversation=is_new,
        resume_value=resume_value,
    )
    return create_sse_response(generator)


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List conversations for the authenticated user (paginated)."""
    clamped_limit = min(max(limit, 1), 100)
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(clamped_limit)
        .offset(max(offset, 0))
    )
    conversations = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "status": c.status,
            "current_phase": c.current_phase,
            "application_id": str(c.application_id) if c.application_id else None,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msgs_result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tool_name": m.tool_name,
            "tool_data": m.tool_data,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
