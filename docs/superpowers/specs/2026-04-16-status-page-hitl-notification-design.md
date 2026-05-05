# Customer Status Page + HITL Notification Flow

**Date:** 2026-04-16
**Branch:** feature/v4-langgraph-sso-frontend
**Status:** Approved for implementation

## Problem

After a customer submits their loan application via the chat interface, they have no way to:
1. Track their application progress outside of the chat
2. See the officer's decision when it arrives
3. View past applications or resume previous conversations

The officer dashboard exists (`/dashboard`) and works, but the officer's approve/deny decision never flows back to the customer.

## Decisions Made

- **Layout:** Option C — Horizontal stepper + status card + quick stats (see mockups in `.superpowers/brainstorm/`)
- **Decision states:** Under Review (amber), Approved (green + offer CTA), Denied (red + reasons with re-apply timeline)
- **Notification:** Polling (15s) + chat message injection — no new infra needed
- **Scope:** Application list + detail with chat link (`/status` → `/status/[id]` → links back to `/chat/[id]`)

## Architecture

### New Frontend Pages

#### `/status` — Application List
- Lists all applications for the logged-in user, newest first
- Each row: reference number, loan amount, status badge (Under Review / Approved / Denied), date, "View" link
- Empty state: "No applications yet — start a conversation to apply"
- Nav: accessible from chat layout header ("My Applications" link)

#### `/status/[id]` — Application Detail
- **Horizontal stepper** at top: Info → Docs → AI Check → Review → Decision
  - Completed steps: green check
  - Current step: gold with glow ring
  - Future steps: gray, 40% opacity
- **Status card** below stepper (changes by state):
  - **Under Review:** Amber gradient, "A credit officer is reviewing your application. Expected decision within 2-3 business days."
  - **Approved:** Green gradient, loan terms (amount, rate, tenure, EMI, total interest), "Accept Offer & Proceed to e-Sign" CTA button
  - **Denied:** Red gradient, denial reasons list, re-apply timeline ("You may re-apply after 6 months"), support contact
- **Quick stats row:** Loan amount, tenure, documents uploaded count
- **"Open Conversation" button:** Links to `/chat/[conversation_id]`
- **Polling:** Fetches status every 15 seconds while on "Under Review"

#### `/chat/[id]` — Resume Conversation
- Same `ChatInterface` component, but initialized with existing `conversation_id`
- Loads message history from `GET /api/v1/chat/conversations/{id}/messages`
- Passes `conversation_id` to the chat stream transport so messages go to the right thread

### New Backend APIs

#### `GET /api/v1/status/applications`
- **Auth:** JWT required, scoped to `user.id`
- **Response:** Array of applications with:
  ```json
  [
    {
      "id": "uuid",
      "reference_number": "LN-28A4F3",
      "loan_amount": 500000,
      "loan_type": "personal",
      "status": "processing",
      "current_phase": "human_review",
      "decision": null,
      "conversation_id": "uuid",
      "created_at": "2026-04-16T10:00:00Z",
      "updated_at": "2026-04-16T11:30:00Z"
    }
  ]
  ```
- **Query:** Join `applications` + `conversations` (via `conversation.application_id`) + left join `decisions`
- Filter by `application.user_id == current_user.id`

#### `GET /api/v1/status/applications/{id}`
- **Auth:** JWT required, user must own the application
- **Response:**
  ```json
  {
    "id": "uuid",
    "reference_number": "LN-28A4F3",
    "loan_amount": 500000,
    "loan_type": "personal",
    "tenure_months": 36,
    "status": "decided",
    "phase_history": [
      {"phase": "intake", "completed_at": "2026-04-16T10:00:00Z"},
      {"phase": "doc_collection", "completed_at": "2026-04-16T10:05:00Z"},
      {"phase": "doc_verification", "completed_at": "2026-04-16T10:06:00Z"},
      {"phase": "risk_assessment", "completed_at": "2026-04-16T10:06:30Z"},
      {"phase": "human_review", "completed_at": "2026-04-16T12:00:00Z"}
    ],
    "current_phase": "decision",
    "documents": [
      {"type": "pan_card", "status": "completed", "uploaded_at": "..."},
      {"type": "aadhaar", "status": "completed", "uploaded_at": "..."}
    ],
    "decision": {
      "result": "approved",
      "reasons": ["Strong credit score", "Low DTI"],
      "confidence": 0.87,
      "decided_at": "2026-04-16T12:00:00Z"
    },
    "offer": {
      "interest_rate": 11.5,
      "emi_amount": 16720,
      "tenure_months": 36,
      "processing_fee": 5000,
      "total_cost": 601920,
      "accepted": false
    },
    "conversation_id": "uuid"
  }
  ```

### Backend Changes to Existing Code

#### 1. Create Application during chat intake
**Where:** `src/api/routes/chat.py` (after persisting the user message, before streaming)
**What:**
- The frontend sends form data as a JSON text message: `{"tool": "collect_basic_info", "full_name": "...", ...}`
- In the chat route, detect this pattern by checking if `user_text` starts with `{` and contains `"tool": "collect_basic_info"`
- Parse the JSON and create `Application` + `ApplicantProfile` rows
- Generate `reference_number` (format: `LN-{8 uppercase hex chars}`)
- Set `conversation.application_id` to link them
- Set `application.user_id` to the current user

#### 2. Persist graph phase transitions
**Where:** `src/chat/stream.py` (in the stream loop when `current_phase` updates are received)
**What:**
- When a `data-status` event with a new phase is emitted, append to a `phase_history` JSONB column on the Application
- Each entry: `{"phase": "...", "completed_at": "ISO timestamp"}`

#### 3. Persist AI decision to DB
**Where:** `src/chat/stream.py` (when the decision node emits `data-tool-show_decision`)
**What:**
- Extract decision, reasons, confidence from the tool call args
- Create `CreditDecision` row linked to the application
- Update `application.status` to `DECIDED`

#### 4. Persist offer to DB
**Where:** `src/chat/stream.py` (when offer_generation emits `data-tool-show_offer`)
**What:**
- Extract interest_rate, emi_amount, tenure, processing_fee, total_cost from tool call args
- Create `Offer` row linked to the application

#### 5. HITL review injects chat message
**Where:** `src/api/routes/hitl.py` POST `/{id}/review`
**What (after existing logic):**
- Look up `Conversation` where `conversation.application_id == application_id`
- Insert a `ChatMessage` with role="assistant":
  - Approved: "Great news! Your loan application has been approved. Visit your status page to view the offer details and accept."
  - Denied: "We regret to inform you that your loan application was not approved at this time. Please check your status page for details."
- Update `application.status` to `DECIDED`
- Create `CreditDecision` row from the officer's decision

#### 6. Link orphaned documents
**Where:** `src/api/routes/chat.py` (when Application is created in step 1)
**What:**
- Query `Document` where `application_id IS NULL` and the `file_path` contains `user_{user_id}`
- Update their `application_id` to the newly created application

#### 7. Add phase_history column to Application
**Where:** `src/db/models.py`
**What:** Add `phase_history: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)` to Application model

### DB Schema Change

```sql
-- Add phase_history to Application model (user_id FK already exists)
ALTER TABLE applications ADD COLUMN phase_history JSONB;
```

This is a single column addition. Tables are created via `create_all()` so the model change is sufficient — no Alembic migration needed for dev.

## Error Handling

- `/status/[id]` returns 404 gracefully ("Application not found") if ID is invalid or user doesn't own it
- Polling stops after decision is received (no need to keep polling once approved/denied)
- If HITL chat message injection fails (e.g., no conversation found), log error but don't fail the review — officer action is the priority

## Testing

- Unit test: `GET /api/v1/status/applications` returns only the current user's applications
- Unit test: `GET /api/v1/status/applications/{id}` returns 403 for wrong user
- Unit test: HITL review creates ChatMessage in the right conversation
- Integration test: Full flow — create conversation → submit form → check /status shows application → officer reviews → /status shows decision

## Visual Reference

Mockups saved in `.superpowers/brainstorm/` directory:
- `status-layout.html` — Layout options (Option C selected)
- `status-states.html` — Decision state variations (all 3 approved)
