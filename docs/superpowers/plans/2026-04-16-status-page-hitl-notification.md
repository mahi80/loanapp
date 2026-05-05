# Status Page + HITL Notification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a customer status page showing loan application progress, and connect officer HITL decisions back to the customer via polling + chat message injection.

**Architecture:** New `/status` and `/status/[id]` frontend pages poll a new `GET /api/v1/status/applications` backend API. Chat route creates Application records when basic info form is submitted. Stream function persists phase transitions, decisions, and offers to DB. HITL review endpoint injects an assistant message into the customer's conversation.

**Tech Stack:** FastAPI, SQLAlchemy, Next.js 16, React 19, shadcn/ui, Tailwind CSS 4, Framer Motion

---

### Task 1: Add phase_history column to Application model

**Files:**
- Modify: `src/db/models.py:161-180`
- Test: `tests/test_db/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_db/test_models.py — add at bottom
def test_application_has_phase_history():
    from src.db.models import Application
    cols = {c.name for c in Application.__table__.columns}
    assert "phase_history" in cols
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db/test_models.py::test_application_has_phase_history -v`
Expected: FAIL — `phase_history` not in columns

- [ ] **Step 3: Add phase_history to Application model**

In `src/db/models.py`, after line 180 (`reference_number` field), add:

```python
    phase_history: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db/test_models.py::test_application_has_phase_history -v`
Expected: PASS

- [ ] **Step 5: Recreate DB tables in Docker**

```bash
docker compose exec app python -c "
from src.db.models import Base
from sqlalchemy import create_engine
engine = create_engine('postgresql://loan:loan@postgres:5432/loan_underwriting')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print('Tables recreated')
"
```

- [ ] **Step 6: Commit**

```bash
git add src/db/models.py tests/test_db/test_models.py
git commit -m "feat: add phase_history JSONB column to Application model"
```

---

### Task 2: Backend status API routes

**Files:**
- Create: `src/api/routes/status.py`
- Modify: `src/main.py` (register router)
- Test: `tests/test_api/test_status.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_api/test_status.py`:

```python
from src.api.routes.status import router


def test_status_router_has_list_endpoint():
    paths = [r.path for r in router.routes]
    assert any("applications" in str(p) for p in paths)


def test_status_router_has_detail_endpoint():
    paths = [r.path for r in router.routes]
    assert any("{application_id}" in str(p) for p in paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api/test_status.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Create status route file**

Create `src/api/routes/status.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.db.session import get_db
from src.db.models import (
    Application, Conversation, CreditDecision, Document, Offer, User,
)
from src.auth.middleware import get_current_user

router = APIRouter(prefix="/api/v1/status", tags=["status"])


class ApplicationListItem(BaseModel):
    id: uuid.UUID
    reference_number: str | None
    loan_amount: float
    loan_type: str
    status: str
    current_phase: str | None
    decision: str | None
    conversation_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhaseEntry(BaseModel):
    phase: str
    completed_at: str


class DocumentEntry(BaseModel):
    type: str
    status: str
    uploaded_at: str | None


class DecisionDetail(BaseModel):
    result: str
    reasons: list[str]
    confidence: float
    decided_at: str


class OfferDetail(BaseModel):
    interest_rate: float
    emi_amount: float
    tenure_months: int
    processing_fee: float
    total_cost: float
    accepted: bool


class ApplicationDetail(BaseModel):
    id: uuid.UUID
    reference_number: str | None
    loan_amount: float
    loan_type: str
    tenure_months: int | None
    status: str
    phase_history: list[PhaseEntry]
    current_phase: str | None
    documents: list[DocumentEntry]
    decision: DecisionDetail | None
    offer: OfferDetail | None
    conversation_id: uuid.UUID | None

    model_config = {"from_attributes": True}


@router.get("/applications", response_model=list[ApplicationListItem])
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all loan applications for the authenticated customer."""
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.created_at.desc())
    )
    apps = result.scalars().all()

    items = []
    for app in apps:
        # Find linked conversation
        conv_result = await db.execute(
            select(Conversation).where(Conversation.application_id == app.id)
        )
        conv = conv_result.scalar_one_or_none()

        # Find decision
        dec_result = await db.execute(
            select(CreditDecision).where(CreditDecision.application_id == app.id)
        )
        dec = dec_result.scalar_one_or_none()

        items.append(ApplicationListItem(
            id=app.id,
            reference_number=app.reference_number,
            loan_amount=float(app.loan_amount),
            loan_type=app.loan_type.value,
            status=app.status.value,
            current_phase=app.phase_history[-1]["phase"] if app.phase_history else None,
            decision=dec.decision.value if dec else None,
            conversation_id=conv.id if conv else None,
            created_at=app.created_at,
            updated_at=app.updated_at,
        ))

    return items


@router.get("/applications/{application_id}", response_model=ApplicationDetail)
async def get_application_detail(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full application detail for the status page stepper."""
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.application_id == app.id)
    )
    conv = conv_result.scalar_one_or_none()

    # Documents
    doc_result = await db.execute(
        select(Document).where(Document.application_id == app.id)
    )
    docs = doc_result.scalars().all()

    # Decision
    dec_result = await db.execute(
        select(CreditDecision).where(CreditDecision.application_id == app.id)
    )
    dec = dec_result.scalar_one_or_none()

    # Offer
    offer_result = await db.execute(
        select(Offer).where(Offer.application_id == app.id)
    )
    offer = offer_result.scalar_one_or_none()

    return ApplicationDetail(
        id=app.id,
        reference_number=app.reference_number,
        loan_amount=float(app.loan_amount),
        loan_type=app.loan_type.value,
        tenure_months=app.tenure_months,
        status=app.status.value,
        phase_history=[
            PhaseEntry(phase=p["phase"], completed_at=p["completed_at"])
            for p in (app.phase_history or [])
        ],
        current_phase=app.phase_history[-1]["phase"] if app.phase_history else "intake",
        documents=[
            DocumentEntry(
                type=d.type.value,
                status=d.ocr_status.value,
                uploaded_at=d.uploaded_at.isoformat() if d.uploaded_at else None,
            )
            for d in docs
        ],
        decision=DecisionDetail(
            result=dec.decision.value,
            reasons=dec.conditions.get("reasons", []) if dec.conditions else [],
            confidence=dec.confidence,
            decided_at=dec.decided_at.isoformat(),
        ) if dec else None,
        offer=OfferDetail(
            interest_rate=float(offer.application.decision.interest_rate) if offer and offer.application and offer.application.decision else 0,
            emi_amount=float(offer.emi_schedule.get("emi", 0)) if offer and offer.emi_schedule else 0,
            tenure_months=app.tenure_months or 0,
            processing_fee=float(offer.total_cost or 0) * 0.01 if offer else 0,
            total_cost=float(offer.total_cost or 0) if offer else 0,
            accepted=offer.accepted if offer else False,
        ) if offer else None,
        conversation_id=conv.id if conv else None,
    )
```

- [ ] **Step 4: Register router in main.py**

In `src/main.py`, add after the existing route imports:

```python
from src.api.routes.status import router as status_router
```

And after `app.include_router(notifications.router)`:

```python
app.include_router(status_router)
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_api/test_status.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/api/routes/status.py src/main.py tests/test_api/test_status.py
git commit -m "feat: add GET /api/v1/status/applications list and detail endpoints"
```

---

### Task 3: Create Application when basic info form is submitted

**Files:**
- Modify: `src/api/routes/chat.py:58-163`
- Test: `tests/test_chat/test_routes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_chat/test_routes.py`:

```python
from src.api.routes.chat import _try_create_application_from_form


def test_detect_basic_info_form():
    import json
    form_text = json.dumps({
        "tool": "collect_basic_info",
        "full_name": "Raj Kumar",
        "pan_number": "ABCDE1234F",
        "date_of_birth": "1990-03-15",
        "mobile": "9876543210",
        "email": "raj@example.com",
        "employment_type": "salaried",
        "monthly_income": 75000,
        "employer": "TCS",
        "city": "Mumbai",
    })
    parsed = _try_create_application_from_form(form_text)
    assert parsed is not None
    assert parsed["full_name"] == "Raj Kumar"
    assert parsed["pan_number"] == "ABCDE1234F"


def test_non_form_message_returns_none():
    parsed = _try_create_application_from_form("I want a loan")
    assert parsed is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat/test_routes.py::test_detect_basic_info_form -v`
Expected: FAIL — cannot import `_try_create_application_from_form`

- [ ] **Step 3: Add form detection and application creation to chat.py**

Add this function after `_extract_user_message` in `src/api/routes/chat.py`:

```python
def _try_create_application_from_form(user_text: str) -> dict | None:
    """Detect if user_text is a basic info form submission. Returns parsed form data or None."""
    if not user_text.strip().startswith("{"):
        return None
    try:
        data = json.loads(user_text)
        if data.get("tool") == "collect_basic_info" and data.get("pan_number"):
            return data
        return None
    except (json.JSONDecodeError, AttributeError):
        return None
```

Then in the `chat_stream` function, add application creation after `await db.flush()` (after persisting user_msg, around line 112). Add these imports at top:

```python
from src.db.models import User, Conversation, ChatMessage, Application, ApplicantProfile, ApplicationStatus, LoanType, EmploymentType, Document
```

And the creation logic after `await db.flush()` for user_msg:

```python
    # Detect basic info form submission and create Application
    form_data = _try_create_application_from_form(user_text)
    if form_data and not conversation.application_id:
        ref = f"LN-{uuid.uuid4().hex[:8].upper()}"
        emp_type = None
        if form_data.get("employment_type") in ("salaried", "self_employed"):
            emp_type = EmploymentType(form_data["employment_type"])

        application = Application(
            applicant_name=form_data.get("full_name", ""),
            pan_number=form_data.get("pan_number", ""),
            mobile=form_data.get("mobile"),
            loan_amount=form_data.get("monthly_income", 0) * 10,  # Placeholder until loan details
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
                Document.file_path.contains(f"user_{user.id}"),
            )
        )
        for doc in orphan_result.scalars().all():
            doc.application_id = application.id
```

Add `from datetime import datetime, UTC` to the imports at top.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_chat/test_routes.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/chat.py tests/test_chat/test_routes.py
git commit -m "feat: create Application record when basic info form is submitted in chat"
```

---

### Task 4: Persist phase transitions, decisions, and offers during streaming

**Files:**
- Modify: `src/chat/stream.py:83-149`

- [ ] **Step 1: Update stream function to persist phase, decision, and offer**

In `src/chat/stream.py`, add `application_id` parameter to the function signature:

```python
async def stream_langgraph_response(
    state: LoanApplicationState,
    thread_id: str,
    conversation_id: uuid.UUID | None = None,
    application_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
    is_new_conversation: bool = True,
    latest_message=None,
) -> AsyncGenerator[str, None]:
```

Then after the `yield format_data_event("status", ...)` line (around line 125), add phase persistence:

```python
                    if phase and db and application_id:
                        try:
                            from src.db.models import Application as AppModel
                            from datetime import datetime, UTC
                            app_result = await db.execute(
                                select(AppModel).where(AppModel.id == application_id)
                            )
                            app = app_result.scalar_one_or_none()
                            if app:
                                history = app.phase_history or []
                                if not any(p["phase"] == phase for p in history):
                                    history.append({"phase": phase, "completed_at": datetime.now(UTC).isoformat()})
                                    app.phase_history = history
                                    from sqlalchemy.orm.attributes import flag_modified
                                    flag_modified(app, "phase_history")
                        except Exception as e:
                            logger.error("persist_phase_failed", error=str(e))
```

In the tool call collection loop (around line 121), after `collected_tools.append(...)`, add decision and offer persistence:

```python
                                # Persist decision to DB
                                if tool_name == "show_decision" and db and application_id:
                                    try:
                                        from src.db.models import CreditDecision, DecisionEnum, Application as AppModel, ApplicationStatus
                                        from datetime import datetime, UTC
                                        dec = CreditDecision(
                                            application_id=application_id,
                                            decision=DecisionEnum(tool_args.get("decision", "escalated")),
                                            confidence=tool_args.get("confidence", 0.0),
                                            conditions={"reasons": tool_args.get("reasons", [])},
                                        )
                                        db.add(dec)
                                        app_r = await db.execute(select(AppModel).where(AppModel.id == application_id))
                                        app_obj = app_r.scalar_one_or_none()
                                        if app_obj:
                                            app_obj.status = ApplicationStatus.DECIDED
                                    except Exception as e:
                                        logger.error("persist_decision_failed", error=str(e))

                                # Persist offer to DB
                                if tool_name == "show_offer" and db and application_id:
                                    try:
                                        from src.db.models import Offer as OfferModel
                                        offer = OfferModel(
                                            application_id=application_id,
                                            emi_schedule={
                                                "emi": tool_args.get("emi_amount", 0),
                                                "rate": tool_args.get("interest_rate", 0),
                                            },
                                            total_cost=tool_args.get("total_cost", 0),
                                        )
                                        db.add(offer)
                                    except Exception as e:
                                        logger.error("persist_offer_failed", error=str(e))
```

- [ ] **Step 2: Pass application_id from chat route**

In `src/api/routes/chat.py`, update the `stream_langgraph_response` call to pass `application_id`:

```python
    generator = stream_langgraph_response(
        state=state,
        thread_id=conversation.langgraph_thread_id or f"thread_{conversation.id}",
        conversation_id=conversation.id,
        application_id=conversation.application_id,
        db=db,
        is_new_conversation=is_new,
        latest_message=latest_message,
    )
```

- [ ] **Step 3: Add the select import to stream.py**

Add at top of `src/chat/stream.py`:

```python
from sqlalchemy import select
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -x -q`
Expected: 134+ passed

- [ ] **Step 5: Commit**

```bash
git add src/chat/stream.py src/api/routes/chat.py
git commit -m "feat: persist phase transitions, decisions, and offers during LangGraph streaming"
```

---

### Task 5: HITL review injects chat message into customer conversation

**Files:**
- Modify: `src/api/routes/hitl.py:82-109`
- Test: `tests/test_chat/test_routes.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_chat/test_routes.py`:

```python
def test_hitl_review_messages():
    """Verify HITL message templates exist."""
    from src.api.routes.hitl import _DECISION_MESSAGES
    assert "approved" in _DECISION_MESSAGES
    assert "denied" in _DECISION_MESSAGES
    assert "status page" in _DECISION_MESSAGES["approved"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat/test_routes.py::test_hitl_review_messages -v`
Expected: FAIL — cannot import `_DECISION_MESSAGES`

- [ ] **Step 3: Add chat message injection to hitl.py**

Add at module level in `src/api/routes/hitl.py`, after the imports:

```python
from src.db.models import Application, ApplicationStatus, CreditDecision, HITLReview, AgentOutput, DecisionEnum, CreditScore, User, Conversation, ChatMessage

_DECISION_MESSAGES = {
    "approved": "Great news! Your loan application has been approved. Visit your status page to view the offer details and accept.",
    "denied": "We regret to inform you that your loan application was not approved at this time. Please check your status page for details.",
    "conditional": "Your loan application has been conditionally approved. Please check your status page for the conditions and next steps.",
    "escalated": "Your application requires additional review. We will notify you once a decision has been made.",
}
```

Then in `submit_review`, after the existing `app.status = ApplicationStatus.DECIDED` block (around line 106), add:

```python
    # Create CreditDecision from officer review
    dec = CreditDecision(
        application_id=application_id,
        decision=review.decision,
        confidence=1.0,
        rationale=review.officer_notes,
        conditions={"reasons": [review.override_reason]} if review.override_reason else None,
    )
    db.add(dec)

    # Inject assistant message into customer conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.application_id == application_id)
    )
    conv = conv_result.scalar_one_or_none()
    if conv:
        msg_text = _DECISION_MESSAGES.get(review.decision.value, _DECISION_MESSAGES["escalated"])
        chat_msg = ChatMessage(
            conversation_id=conv.id,
            role="assistant",
            content=msg_text,
        )
        db.add(chat_msg)
```

Also update the existing import line to include `Conversation` and `ChatMessage` (they should already be there from the earlier fix but verify).

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_chat/test_routes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/hitl.py tests/test_chat/test_routes.py
git commit -m "feat: HITL review injects decision message into customer conversation"
```

---

### Task 6: Frontend — /status application list page

**Files:**
- Create: `frontend/src/app/status/layout.tsx`
- Create: `frontend/src/app/status/page.tsx`
- Create: `frontend/src/components/status/application-list.tsx`

- [ ] **Step 1: Create status layout**

Create `frontend/src/app/status/layout.tsx`:

```tsx
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { SignOutButton } from "@/components/auth/sign-out-button";
import { UserAvatar } from "@/components/auth/user-avatar";

export default async function StatusLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <div className="h-screen flex flex-col bg-[#FAFBFC]">
      <header className="h-16 border-b border-slate-200 bg-white flex items-center px-6 shrink-0">
        <Image src="/images/logo-light.svg" alt="LoanAI" width={120} height={32} />
        <nav className="ml-8 flex items-center gap-6">
          <Link href="/chat" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">Chat</Link>
          <Link href="/status" className="text-sm text-[#0F172A] font-semibold border-b-2 border-[#D4A853] pb-0.5">My Applications</Link>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-slate-600 font-medium">{session.user?.name}</span>
          <UserAvatar name={session.user?.name} image={session.user?.image} />
          <SignOutButton />
        </div>
      </header>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Create application list component**

Create `frontend/src/components/status/application-list.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, ArrowRight } from "lucide-react";
import { apiClient } from "@/lib/api";

interface ApplicationItem {
  id: string;
  reference_number: string | null;
  loan_amount: number;
  loan_type: string;
  status: string;
  current_phase: string | null;
  decision: string | null;
  conversation_id: string | null;
  created_at: string;
}

const statusBadge: Record<string, { label: string; className: string }> = {
  approved: { label: "Approved", className: "bg-green-100 text-green-700" },
  denied: { label: "Denied", className: "bg-red-100 text-red-700" },
  conditional: { label: "Conditional", className: "bg-blue-100 text-blue-700" },
};

function getStatusBadge(decision: string | null, status: string) {
  if (decision && statusBadge[decision]) return statusBadge[decision];
  if (status === "decided") return { label: "Decided", className: "bg-slate-100 text-slate-700" };
  return { label: "Under Review", className: "bg-amber-100 text-amber-700" };
}

export function ApplicationList() {
  const { data: session } = useSession();
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    apiClient("/api/v1/status/applications", { token })
      .then(setApps)
      .catch(() => setApps([]))
      .finally(() => setLoading(false));
  }, [session]);

  if (loading) return <div className="p-12 text-center text-slate-400">Loading applications...</div>;

  if (apps.length === 0) {
    return (
      <div className="p-12 text-center">
        <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-slate-700 mb-2">No applications yet</h3>
        <p className="text-slate-500 text-sm mb-6">Start a conversation to apply for a personal loan.</p>
        <Link href="/chat" className="inline-flex items-center gap-2 bg-[#0F172A] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-[#1E293B] transition-colors">
          Start Application <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {apps.map((app) => {
        const badge = getStatusBadge(app.decision, app.status);
        return (
          <Link key={app.id} href={`/status/${app.id}`}>
            <Card className="hover:border-[#D4A853]/50 hover:shadow-md transition-all cursor-pointer">
              <CardContent className="flex items-center gap-4 py-4">
                <div className="w-10 h-10 rounded-lg bg-[#0F172A]/5 flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-[#0F172A]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm text-[#0F172A]">{app.reference_number || app.id.slice(0, 8)}</p>
                  <p className="text-xs text-slate-500">
                    {app.loan_type.charAt(0).toUpperCase() + app.loan_type.slice(1)} Loan
                    {" "}&middot;{" "}
                    {new Date(app.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-semibold text-sm text-[#0F172A]">
                    {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(app.loan_amount)}
                  </p>
                </div>
                <Badge className={`shrink-0 ${badge.className}`}>{badge.label}</Badge>
                <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
              </CardContent>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Create status page**

Create `frontend/src/app/status/page.tsx`:

```tsx
import { ApplicationList } from "@/components/status/application-list";

export default function StatusPage() {
  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-1">My Applications</h1>
        <p className="text-slate-500 text-sm mb-6">Track the progress of your loan applications</p>
        <ApplicationList />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/status/layout.tsx frontend/src/app/status/page.tsx frontend/src/components/status/application-list.tsx
git commit -m "feat: add /status page with application list"
```

---

### Task 7: Frontend — /status/[id] application detail page with stepper

**Files:**
- Create: `frontend/src/app/status/[id]/page.tsx`
- Create: `frontend/src/components/status/application-detail.tsx`
- Create: `frontend/src/components/status/phase-stepper.tsx`
- Create: `frontend/src/components/status/status-card.tsx`

- [ ] **Step 1: Create PhaseStepper component**

Create `frontend/src/components/status/phase-stepper.tsx`:

```tsx
"use client";

const PHASES = [
  { key: "intake", label: "Info" },
  { key: "doc_collection", label: "Docs" },
  { key: "doc_verification", label: "AI Check" },
  { key: "human_review", label: "Review" },
  { key: "decision", label: "Decision" },
];

interface PhaseStepperProps {
  completedPhases: string[];
  currentPhase: string;
  decision?: string | null;
}

export function PhaseStepper({ completedPhases, currentPhase, decision }: PhaseStepperProps) {
  const completedSet = new Set(completedPhases);

  return (
    <div className="flex items-center justify-between px-2">
      {PHASES.map((phase, i) => {
        const isCompleted = completedSet.has(phase.key);
        const isCurrent = phase.key === currentPhase;
        const isDenied = phase.key === "decision" && decision === "denied";
        const isApproved = phase.key === "decision" && (decision === "approved" || decision === "conditional");

        let bgColor = "bg-slate-200";
        let textColor = "text-slate-400";
        let icon = String(i + 1);
        let ringClass = "";

        if (isCompleted || isApproved) {
          bgColor = "bg-[#22c55e]";
          textColor = "text-[#22c55e]";
          icon = "\u2713";
        } else if (isDenied) {
          bgColor = "bg-[#ef4444]";
          textColor = "text-[#ef4444]";
          icon = "\u2715";
        } else if (isCurrent) {
          bgColor = "bg-[#D4A853]";
          textColor = "text-[#D4A853]";
          ringClass = "ring-4 ring-[#D4A853]/20";
        }

        const lineCompleted = isCompleted || (i < PHASES.length - 1 && completedSet.has(PHASES[i + 1]?.key));

        return (
          <div key={phase.key} className="flex items-center" style={{ flex: i < PHASES.length - 1 ? 1 : undefined }}>
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full ${bgColor} text-white flex items-center justify-center text-xs font-bold ${ringClass}`}>
                {icon}
              </div>
              <span className={`text-[10px] mt-1.5 font-medium ${isCurrent ? textColor + " font-semibold" : textColor}`}>
                {phase.label}
              </span>
            </div>
            {i < PHASES.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 mt-[-14px] ${lineCompleted ? "bg-[#22c55e]" : isCurrent ? "bg-[#D4A853]" : "bg-slate-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Create StatusCard component**

Create `frontend/src/components/status/status-card.tsx`:

```tsx
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

interface StatusCardProps {
  decision: string | null;
  offer?: {
    interest_rate: number;
    emi_amount: number;
    tenure_months: number;
    processing_fee: number;
    total_cost: number;
    accepted: boolean;
  } | null;
  reasons?: string[];
  loanAmount?: number;
}

export function StatusCard({ decision, offer, reasons, loanAmount }: StatusCardProps) {
  if (decision === "approved" || decision === "conditional") {
    return (
      <div className="bg-gradient-to-br from-[#f0fdf4] to-[#ecfdf5] border border-[#86efac] rounded-xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-2xl">🎉</span>
          <div>
            <h3 className="font-bold text-lg text-[#166534]">Loan Approved!</h3>
            {offer && (
              <p className="text-sm text-[#4ade80]">
                {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(loanAmount || 0)}
                {" "}at {offer.interest_rate}% p.a. for {offer.tenure_months} months
              </p>
            )}
          </div>
        </div>
        {offer && (
          <>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-white rounded-lg p-3 text-center border border-[#dcfce7]">
                <p className="text-lg font-bold text-[#0F172A]">
                  {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(offer.emi_amount)}
                </p>
                <p className="text-xs text-slate-500">Monthly EMI</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center border border-[#dcfce7]">
                <p className="text-lg font-bold text-[#0F172A]">
                  {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(offer.total_cost - (loanAmount || 0))}
                </p>
                <p className="text-xs text-slate-500">Total Interest</p>
              </div>
            </div>
            {!offer.accepted && (
              <Button className="w-full bg-[#166534] hover:bg-[#15803d] text-white font-semibold">
                Accept Offer & Proceed to e-Sign →
              </Button>
            )}
          </>
        )}
      </div>
    );
  }

  if (decision === "denied") {
    return (
      <div className="bg-gradient-to-br from-[#fef2f2] to-[#fff1f2] border border-[#fca5a5] rounded-xl p-5">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">📋</span>
          <div>
            <h3 className="font-semibold text-[#991b1b]">Application Not Approved</h3>
            <p className="text-sm text-[#b91c1c]">We&apos;re unable to approve your application at this time.</p>
          </div>
        </div>
        {reasons && reasons.length > 0 && (
          <div className="mb-3">
            <p className="text-sm font-semibold text-[#7f1d1d] mb-1">Reasons:</p>
            <ul className="list-disc pl-5 text-sm text-[#991b1b] space-y-0.5">
              {reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        <p className="text-xs text-slate-500 border-t border-[#fecaca] pt-3">
          You may re-apply after 6 months. Contact support@loanai.in for queries.
        </p>
      </div>
    );
  }

  // Default: Under Review
  return (
    <div className="bg-gradient-to-br from-[#fefce8] to-[#fff7ed] border border-[#fde68a] rounded-xl p-5">
      <div className="flex items-center gap-3">
        <span className="text-2xl">⏳</span>
        <div>
          <h3 className="font-semibold text-[#92400e]">Under Officer Review</h3>
          <p className="text-sm text-[#78716c]">
            A credit officer is reviewing your application. Expected decision within 2-3 business days.
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create ApplicationDetail component with polling**

Create `frontend/src/components/status/application-detail.tsx`:

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { PhaseStepper } from "./phase-stepper";
import { StatusCard } from "./status-card";
import { apiClient } from "@/lib/api";
import { MessageSquare, ArrowLeft } from "lucide-react";

interface Props {
  applicationId: string;
}

export function ApplicationDetail({ applicationId }: Props) {
  const { data: session } = useSession();
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchDetail = useCallback(async () => {
    if (!session) return;
    const token = (session as any)?.backendToken as string;
    try {
      const data = await apiClient(`/api/v1/status/applications/${applicationId}`, { token });
      setDetail(data);
    } catch {
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [session, applicationId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // Poll every 15s while under review
  useEffect(() => {
    if (!detail || detail.decision) return;
    const interval = setInterval(fetchDetail, 15000);
    return () => clearInterval(interval);
  }, [detail, fetchDetail]);

  if (loading) return <div className="p-12 text-center text-slate-400">Loading...</div>;
  if (!detail) return <div className="p-12 text-center text-red-500">Application not found</div>;

  const completedPhases = (detail.phase_history || []).map((p: any) => p.phase);
  const currentPhase = detail.current_phase || "intake";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/status" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-2">
            <ArrowLeft className="w-4 h-4" /> Back to applications
          </Link>
          <h1 className="text-xl font-bold text-[#0F172A]">{detail.reference_number || "Application"}</h1>
        </div>
        {detail.conversation_id && (
          <Link href={`/chat/${detail.conversation_id}`}>
            <Button variant="outline" className="gap-2">
              <MessageSquare className="w-4 h-4" /> Open Conversation
            </Button>
          </Link>
        )}
      </div>

      {/* Stepper */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <PhaseStepper
          completedPhases={completedPhases}
          currentPhase={currentPhase}
          decision={detail.decision?.result}
        />
      </div>

      {/* Status Card */}
      <StatusCard
        decision={detail.decision?.result || null}
        offer={detail.offer}
        reasons={detail.decision?.reasons}
        loanAmount={detail.loan_amount}
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-4 text-center">
          <p className="text-xl font-bold text-[#0F172A]">
            {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(detail.loan_amount)}
          </p>
          <p className="text-xs text-slate-500">Loan Amount</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 text-center">
          <p className="text-xl font-bold text-[#0F172A]">{detail.tenure_months || "—"}mo</p>
          <p className="text-xs text-slate-500">Tenure</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 text-center">
          <p className="text-xl font-bold text-[#0F172A]">{detail.documents?.length || 0}</p>
          <p className="text-xs text-slate-500">Documents</p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create detail page**

Create `frontend/src/app/status/[id]/page.tsx`:

```tsx
"use client";

import { useParams } from "next/navigation";
import { ApplicationDetail } from "@/components/status/application-detail";

export default function StatusDetailPage() {
  const { id } = useParams();
  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="max-w-3xl mx-auto">
        <ApplicationDetail applicationId={id as string} />
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/status/[id]/page.tsx frontend/src/components/status/application-detail.tsx frontend/src/components/status/phase-stepper.tsx frontend/src/components/status/status-card.tsx
git commit -m "feat: add /status/[id] detail page with stepper, status card, and polling"
```

---

### Task 8: Frontend — /chat/[id] resume conversation page

**Files:**
- Create: `frontend/src/app/chat/[id]/page.tsx`
- Modify: `frontend/src/components/chat/chat-interface.tsx`

- [ ] **Step 1: Add conversationId prop to ChatInterface**

In `frontend/src/components/chat/chat-interface.tsx`, update the component to accept an optional conversation ID:

```tsx
interface ChatInterfaceProps {
  conversationId?: string;
}

export function ChatInterface({ conversationId }: ChatInterfaceProps) {
```

Update the transport `useMemo` to include conversation_id in the body:

```tsx
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${API_URL}/api/v1/chat/stream`,
        headers: () => ({
          Authorization: `Bearer ${(sessionRef.current as any)?.backendToken || ""}`,
        }),
        body: conversationId ? { conversation_id: conversationId } : undefined,
      }),
    [conversationId]
  );
```

- [ ] **Step 2: Create /chat/[id] page**

Create `frontend/src/app/chat/[id]/page.tsx`:

```tsx
"use client";

import { useParams } from "next/navigation";
import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatConversationPage() {
  const { id } = useParams();
  return <ChatInterface conversationId={id as string} />;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/chat/[id]/page.tsx frontend/src/components/chat/chat-interface.tsx
git commit -m "feat: add /chat/[id] page for resuming conversations"
```

---

### Task 9: Add "My Applications" navigation link to chat layout

**Files:**
- Modify: `frontend/src/app/chat/layout.tsx`

- [ ] **Step 1: Add nav link**

Update `frontend/src/app/chat/layout.tsx` to add navigation:

```tsx
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { SignOutButton } from "@/components/auth/sign-out-button";
import { UserAvatar } from "@/components/auth/user-avatar";

export default async function ChatLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect("/");

  return (
    <div className="h-screen flex flex-col bg-[#FAFBFC]">
      <header className="h-16 border-b border-slate-200 bg-white flex items-center px-6 shrink-0">
        <Image src="/images/logo-light.svg" alt="LoanAI" width={120} height={32} />
        <nav className="ml-8 flex items-center gap-6">
          <Link href="/chat" className="text-sm text-[#0F172A] font-semibold border-b-2 border-[#D4A853] pb-0.5">Chat</Link>
          <Link href="/status" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">My Applications</Link>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-slate-600 font-medium">{session.user?.name}</span>
          <UserAvatar name={session.user?.name} image={session.user?.image} />
          <SignOutButton />
        </div>
      </header>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/chat/layout.tsx
git commit -m "feat: add My Applications nav link to chat layout header"
```

---

### Task 10: Rebuild Docker and verify end-to-end

**Files:** None (verification only)

- [ ] **Step 1: Run backend tests**

```bash
pytest tests/ -x -q
```

Expected: All tests pass

- [ ] **Step 2: Rebuild Docker containers**

```bash
docker compose up -d --build
```

- [ ] **Step 3: Verify health**

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

Expected: healthy + 200

- [ ] **Step 4: Test status API**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"google_id":"test123","email":"test@test.com","name":"Test","picture":""}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://localhost:8000/api/v1/status/applications \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: `[]` (empty list — no applications yet)

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: verify end-to-end status page + HITL notification flow"
```
