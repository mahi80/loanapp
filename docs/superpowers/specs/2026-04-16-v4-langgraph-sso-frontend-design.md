# V4 Design Spec: LangGraph + Google SSO + Chat-First Frontend

**Date:** 2026-04-16
**Branch:** `feature/v4-langgraph-sso-frontend`
**Status:** Approved

## 1. Overview

Rebuild the Loan Origination Agent from a form-filling backend pipeline into a chat-first, bank-grade application with two interfaces:

- **Customer Portal** — AI-guided conversational loan application with inline rich UI (forms, document upload, verification feedback)
- **Officer Dashboard** — HITL review queue with full AI analysis, approve/reject/request-more-info actions

### Key Changes from V3

| Area | V3 (Current) | V4 (Target) |
|------|-------------|-------------|
| Agent framework | EvoAgentX (prompt-only wrappers) | LangGraph StateGraph with tool bindings |
| Auth | None | Google SSO + JWT |
| Frontend | None | Next.js 15 + Vercel AI SDK + shadcn/ui |
| User flow | REST form submission | Chat-first with inline rich UI |
| Document processing | Mock data in dev | Azure Document Intelligence (real extraction) |
| Prompts | Static templates | Dynamic context-aware assembly |
| Data types | Float for money | Numeric(15,2) |
| Chat persistence | None | Conversation + ChatMessage tables |

### Out of Scope (Future)

- Evolution mechanism (TextGrad/AFlow/MIPRO)
- Email/SMS/WhatsApp notifications
- PII encryption at rest (pgcrypto)
- Multi-language support (Hindi)
- Mobile-optimized UI
- Document malware scanning
- Multi-officer assignment and SLA escalation
- Prometheus/Grafana dashboard integration

---

## 2. Architecture

```
┌─────────────────────────────────────────┐
│  Next.js 15 Frontend                     │
│  ├── /app/chat     (customer portal)     │
│  ├── /app/dashboard (officer HITL)       │
│  ├── /app/status   (application tracker) │
│  ├── /api/auth     (Google SSO + JWT)    │
│  └── /api/chat     (SSE proxy to FastAPI)│
│                                          │
│  Tech: Tailwind CSS + shadcn/ui          │
│        + Vercel AI SDK (useChat)         │
│        + Framer Motion (animations)      │
└──────────────┬───────────────────────────┘
               │ SSE (streaming) + REST
┌──────────────▼───────────────────────────┐
│  FastAPI Backend                          │
│  ├── POST /api/v1/chat/stream            │
│  │   (SSE endpoint, LangGraph events     │
│  │    serialized as Vercel AI SDK format) │
│  ├── Auth middleware (verify JWT)         │
│  ├── LangGraph StateGraph                │
│  │   ├── intake_node                     │
│  │   ├── document_collection_node        │
│  │   ├── document_verification_node      │
│  │   ├── bureau_pull_node                │
│  │   ├── income_verification_node        │
│  │   ├── risk_assessment_node            │
│  │   ├── fraud_detection_node            │
│  │   ├── score_aggregation_node          │
│  │   ├── compliance_node                 │
│  │   ├── pricing_node                    │
│  │   ├── decision_node                   │
│  │   ├── offer_generation_node           │
│  │   └── human_review_node (HITL)        │
│  ├── Tools (bound to nodes)              │
│  │   ├── eligibility_rules               │
│  │   ├── dti_calculator                  │
│  │   ├── risk_scorer                     │
│  │   ├── four_c_scorer                   │
│  │   ├── emi_scheduler                   │
│  │   ├── rate_card_engine                │
│  │   ├── weighted_aggregator             │
│  │   ├── volatility_calculator           │
│  │   ├── hidden_debt_scanner             │
│  │   ├── bias_detector                   │
│  │   ├── negative_list_checker           │
│  │   ├── azure_doc_intelligence          │
│  │   └── bureau_clients (CIBIL, etc.)    │
│  └── HITL review endpoints               │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│  Azure Services                           │
│  ├── PostgreSQL Flexible Server           │
│  │   (rg-loan-underwriting-dev)           │
│  ├── Redis Cache                          │
│  │   (rg-loan-underwriting-dev)           │
│  ├── Blob Storage (stloanuwdocs2026)      │
│  ├── AI Services — Doc Intelligence       │
│  │   (mahen-mlhrtlu0-eastus2)             │
│  ├── AI Services — GPT-5.2               │
│  │   (mahen-mlhrtlu0-eastus2)             │
│  └── AKS Cluster                          │
│      (aks-loan-underwriting-dev)           │
└───────────────────────────────────────────┘
```

---

## 3. Data Model Changes

### 3.1 New Tables

```sql
-- User accounts (Google SSO)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    picture_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'customer',  -- 'customer' | 'officer'
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

-- Chat conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    application_id UUID REFERENCES applications(id),
    status VARCHAR(20) DEFAULT 'active',  -- 'active' | 'completed' | 'paused'
    current_phase VARCHAR(50),
    langgraph_thread_id VARCHAR(255),  -- LangGraph checkpoint thread
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Chat messages (full history)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,  -- 'user' | 'assistant' | 'system' | 'tool'
    content TEXT,
    tool_name VARCHAR(100),      -- if role='tool', which tool rendered
    tool_data JSONB,             -- structured data for inline UI rendering
    metadata JSONB,              -- tokens, latency, model used
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.2 Modifications to Existing Tables

```sql
-- applications: add user_id foreign key
ALTER TABLE applications ADD COLUMN user_id UUID REFERENCES users(id);
ALTER TABLE applications ADD COLUMN reference_number VARCHAR(20) UNIQUE;

-- Fix Float → Numeric for all money columns
-- applications.loan_amount → NUMERIC(15,2)
-- decisions.interest_rate → NUMERIC(5,2)
-- decisions.processing_fee → NUMERIC(15,2)
-- decisions.emi_amount → NUMERIC(15,2)
-- offers.total_cost → NUMERIC(15,2)
-- disbursements.amount → NUMERIC(15,2)

-- Add cascade deletes to all application child tables
```

---

## 4. Authentication

### 4.1 Google SSO Flow

```
Customer/Officer clicks "Sign in with Google"
    → Next.js /api/auth/google (redirect to Google OAuth)
    → Google consent screen
    → Google redirects to /api/auth/google/callback
    → Backend verifies Google token, creates/finds User record
    → Issues JWT (access_token in response, refresh_token in httpOnly cookie)
    → Frontend stores access_token in memory (not localStorage)
    → Redirect: customer → /chat, officer → /dashboard
```

### 4.2 Configuration

- Client ID: `<your-client-id>.apps.googleusercontent.com`
- Redirect URI: `http://localhost:3000/api/auth/google/callback` (dev)
- Client Secret: stored in `.env` only (never committed)

### 4.3 Role Assignment

- Default role on first login: `customer`
- Officers are seeded via a database script or admin API
- Role stored in JWT claims: `{"sub": user_id, "role": "customer|officer", "email": "..."}`

### 4.4 JWT Middleware

- FastAPI middleware validates JWT on all `/api/v1/*` endpoints
- Extracts `user_id` and `role` from claims
- Customer endpoints: user can only access their own applications
- Officer endpoints: require `role == "officer"`

---

## 5. LangGraph Architecture

### 5.1 State Schema

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class LoanApplicationState(TypedDict):
    # Chat
    messages: Annotated[list, add_messages]

    # Applicant
    user_id: str
    application_id: str
    reference_number: str
    applicant_name: str
    pan_number: str
    dob: str
    mobile: str
    email: str
    employment_type: str  # 'salaried' | 'self_employed'
    monthly_income: float
    employer: str
    city: str
    state: str
    loan_amount: float
    loan_type: str
    tenure_months: int

    # Documents
    documents_uploaded: dict     # {doc_type: {path, extracted_data, verified}}
    documents_required: list     # determined by employment_type
    documents_pending: list

    # Verification Results
    pan_verified: bool
    aadhaar_verified: bool
    face_match_score: float
    bureau_reports: dict         # {provider: {score, data}}
    income_verified: dict
    employer_verified: bool

    # Scoring
    four_c_scores: dict
    dti_ratio: float
    stability_score: float
    fraud_flags: list
    composite_score: int
    risk_category: str

    # Decision
    compliance_status: str
    pricing: dict
    decision: str                # approved | conditional | denied | escalated
    decision_rationale: str
    confidence: float
    offer: dict

    # Flow control
    current_phase: str
    needs_human_review: bool
    officer_decision: str
    conversation_complete: bool
```

### 5.2 Graph Topology (13 Nodes)

Consolidated from 22 EvoAgentX agents to 13 LangGraph nodes. Employer verification is handled within `income_verification` (verify employer exists, then verify salary from that employer).

```
                    ┌──────────┐
                    │  intake   │ ← Greet, collect basic info via inline form
                    └────┬─────┘
                         │
                    ┌────▼──────────┐
                    │ doc_collection │ ← Determine required docs, render upload UI
                    └────┬──────────┘
                         │
                    ┌────▼──────────────┐
                    │ doc_verification   │ ← Azure Doc Intelligence + cross-validation
                    └────┬──────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          │
         ┌─────────┐ ┌────────────┐│
         │ bureau  │ │income_     ││
         │ _pull   │ │verification││ ← includes employer verify
         └────┬────┘ └─────┬──────┘│
              │             │       │
              └──────┬──────┘       │
                     ▼              │
                ┌──────────────┐    │
                │ risk_assess  │ ← 4Cs + DTI + volatility + hidden debt
                └────┬────────┘
                         │
                    ┌────▼──────────┐
                    │ fraud_detect  │ ← Identity + document tampering
                    └────┬──────────┘
                         │
                    ┌────▼──────────┐
                    │ score_agg     │ ← Weighted composite 300-900
                    └────┬──────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          │
         ┌──────────┐ ┌───────┐    │
         │compliance│ │pricing│    │
         └────┬─────┘ └───┬───┘    │
              │           │        │
              └─────┬─────┘        │
                    ▼              │
              ┌──────────┐         │
              │ decision │ ← Approve/Deny/Conditional/Escalate
              └────┬─────┘
                   │
          ┌────────┼────────────┐
          ▼                     ▼
    ┌───────────┐        ┌───────────┐
    │offer_gen  │        │human_review│ ← HITL (if escalated)
    └───────────┘        └───────────┘
```

### 5.3 Node Behavior

Each node is a function that:
1. Reads relevant state
2. Assembles a dynamic prompt from base role + current context
3. Calls the LLM with bound tools
4. Updates state with results
5. Emits a chat message (text or tool_call for inline UI)

Example — `intake` node:
- If state has no applicant info → emit `collect_basic_info` tool call (frontend renders form)
- If form submitted → validate, run eligibility check tool, store in state
- If eligible → emit text message + transition to `doc_collection`
- If not eligible → emit rejection explanation + end conversation

### 5.4 Checkpointing

- Use `langgraph-checkpoint-postgres` with the existing Azure PostgreSQL
- Thread ID = `conversation.langgraph_thread_id`
- Enables: resume conversation across browser sessions, replay, debugging

### 5.5 Streaming Protocol

LangGraph events → FastAPI SSE → Vercel AI SDK:

```
LangGraph emits:
  {"event": "on_chat_model_stream", "data": {"chunk": "..."}}
  {"event": "on_tool_start", "data": {"name": "collect_basic_info", "args": {...}}}
  {"event": "on_tool_end", "data": {"name": "collect_basic_info", "result": {...}}}

FastAPI adapter converts to Vercel AI SDK format:
  data: {"type": "text-delta", "textDelta": "..."}
  data: {"type": "tool-call", "toolName": "collect_basic_info", "args": {...}}
  data: {"type": "tool-result", "toolName": "collect_basic_info", "result": {...}}
```

---

## 6. Frontend Design

### 6.1 Tech Stack

- **Next.js 15** (App Router)
- **Tailwind CSS 4** + **shadcn/ui** (component library)
- **Vercel AI SDK** (`useChat` hook, tool rendering, streaming)
- **Framer Motion** (subtle animations, transitions)
- **NextAuth.js v5** (Google SSO integration)
- **Lucide React** (icons)

### 6.2 Pages

| Route | Purpose | Auth |
|-------|---------|------|
| `/` | Landing page with "Sign in with Google" | Public |
| `/chat` | Customer chat interface | Customer |
| `/chat/[conversationId]` | Resume existing conversation | Customer |
| `/status` | Application status tracker | Customer |
| `/dashboard` | Officer review queue | Officer |
| `/dashboard/[applicationId]` | Full application review | Officer |

### 6.3 Inline UI Components (Chat Tool Rendering)

When the AI emits a tool call, the frontend renders the corresponding component:

| Tool Call Name | Component | Description |
|---|---|---|
| `collect_basic_info` | `<BasicInfoForm/>` | Name, PAN, DOB, mobile, employment type, income, loan amount, tenure |
| `upload_document` | `<DocUploadWidget/>` | Drag-and-drop upload with doc type label, file preview, progress bar |
| `show_verification` | `<VerificationCard/>` | Green check / red X with extracted data preview (e.g., "PAN: ABCDE1234F - Verified") |
| `show_eligibility` | `<EligibilityCard/>` | Pass/fail with criteria breakdown |
| `show_progress` | `<ProgressTracker/>` | Step indicator showing current phase |
| `show_score_summary` | `<ScoreSummary/>` | Risk score gauge, 4C breakdown (for officer view only) |
| `show_offer` | `<OfferCard/>` | Loan offer terms: rate, EMI, tenure, total cost |
| `show_decision` | `<DecisionCard/>` | Approved/Denied/Conditional with explanation |
| `request_clarification` | `<ClarificationCard/>` | When AI needs more info, shows specific question with input |

### 6.4 Design Language

- **Color palette:** Deep navy (#0F172A) + white + gold accent (#D4A853) — premium banking feel
- **Typography:** Inter (body) + serif accent for headings — clean, modern, trustworthy
- **Cards:** Subtle shadows, rounded corners (8px), glass-morphism on key elements
- **Animations:** Smooth message entry (fade + slide up), progress bar fills, verification checkmarks animate in
- **Chat bubbles:** AI messages left-aligned (with bank logo avatar), user messages right-aligned. Inline UI components span full width
- **Dark mode:** Not for MVP. Banks prefer light, professional interfaces

### 6.5 Officer Dashboard

- **Queue view:** Table with columns: Reference #, Applicant, Loan Amount, Risk Score, AI Recommendation, Time in Queue
- **Detail view:** Left panel = full application data + AI analysis. Right panel = all agent outputs, scores, document previews. Bottom = action bar (Approve / Reject / Request Info / Reassign)
- **Real-time:** SSE connection for new queue items. Badge count updates live

---

## 7. Azure Document Intelligence Integration

### 7.1 Document Type → Model Mapping

| Document | Azure Model | Extracted Fields |
|----------|-------------|------------------|
| PAN Card | `prebuilt-idDocument` | Name, PAN number, DOB, father's name |
| Aadhaar Card | `prebuilt-idDocument` | Name, Aadhaar number (masked), DOB, address, photo |
| Bank Statement | `prebuilt-document` | Account holder, account number, bank name, transactions, balance |
| Payslip | `prebuilt-document` | Employee name, employer, gross/net salary, deductions |
| Form 16 | `prebuilt-document` | Employer, employee, total income, TDS |
| ITR | `prebuilt-document` | PAN, assessment year, total income, tax paid |
| GST Certificate | `prebuilt-document` | GSTIN, business name, registration date |

### 7.2 Integration Flow

```
User uploads doc in chat
    → File stored in Azure Blob Storage (stloanuwdocs2026)
    → AI shows "Verifying your document..." with spinner
    → Azure Doc Intelligence API call (3-8 seconds)
    → Extract key fields
    → Cross-validate (name on PAN vs name on Aadhaar vs application name)
    → AI shows VerificationCard: "PAN verified. Name: Raj Kumar. DOB: 15-Mar-1990"
    → If issues: "The name on your PAN (Raj Kumar) doesn't match your application (Rajesh Kumar). Please confirm which is correct."
    → Store extracted data in documents.extracted_data (JSONB)
```

### 7.3 Azure Resource

- Use existing AIServices account: `mahen-mlhrtlu0-eastus2` in `itc-ai-agent-rg-ai-services-dev`
- Endpoint and key added to `.env`
- The AIServices kind includes Document Intelligence capability

---

## 8. Chat Flow — Detailed Sequence

### Phase 1: Intake (intake node)

```
AI:  "Welcome to [Bank Name] Personal Loans. I'll guide you through 
      your application. Let's start with your basic details."

      → renders <BasicInfoForm/> inline
         Fields: Full Name, PAN, DOB, Mobile, Email,
                 Employment (Salaried/Self-Employed), Monthly Income,
                 Employer Name, City

User: fills form, submits

AI:  [runs eligibility_rules tool internally]
      → renders <EligibilityCard passed={true}/> 
      "Great news! You're eligible for a personal loan up to ₹XX,XX,XXX.
       How much would you like to apply for?"

      → renders <LoanDetailsForm/> inline
         Fields: Loan Amount, Tenure (12/24/36/48/60 months)

User: fills and submits

AI:  "Perfect. Your application reference is PLN-2026-00142.
      Now let's collect your documents."
      → renders <ProgressTracker step={2} total={6}/>
```

### Phase 2: Document Collection + Verification (doc_collection + doc_verification nodes)

```
AI:  "Based on your profile, I'll need the following documents:"
     → renders document checklist (PAN, Aadhaar, Selfie, Payslip, 
        Bank Statement, Form 16)
     "Let's start with your PAN card."
     → renders <DocUploadWidget type="pan_card"/>

User: uploads PAN image

AI:  → shows spinner: "Verifying your PAN card..."
     → Azure Doc Intelligence extracts data
     → Cross-validates PAN number format, name match
     → renders <VerificationCard status="verified" data={extracted}/>
     "PAN verified successfully. Now please upload your Aadhaar card."
     → renders <DocUploadWidget type="aadhaar"/>

[... repeat for each document ...]

AI:  [if document is blurry/unreadable]
     → renders <VerificationCard status="failed" reason="Image too blurry"/>
     "I couldn't read your bank statement clearly. Please upload a 
      clearer image or the PDF version."
     → renders <DocUploadWidget type="bank_statement"/>
```

### Phase 3: Background Processing (bureau_pull + income_verify + risk_assess + fraud_detect + score_agg)

```
AI:  "All documents verified! I'm now running a comprehensive 
      assessment. This usually takes about a minute."
     → renders <ProgressTracker step={4} total={6} label="Risk Assessment"/>

     [internally: parallel execution of bureau pull, income verification,
      risk scoring, fraud detection, score aggregation]

     [if salaried: verify salary credits in bank statement match payslip]
     [if self-employed: estimate income from bank statement + ITR/GST]
```

### Phase 4: Decision (compliance + pricing + decision nodes)

```
AI:  [if APPROVED]
     → renders <DecisionCard decision="approved"/>
     → renders <OfferCard rate={12.5} emi={22450} tenure={36} 
                           totalCost={808200}/>
     "Congratulations! Your loan has been approved. Here are your 
      offer details."

     [if ESCALATED]
     "Your application has been submitted to our credit review team 
      for final assessment. Reference: PLN-2026-00142. You'll receive 
      an update within 2-3 business days."
     → renders <StatusCard status="under_review"/>
     → conversation.status = 'paused'
     → application appears in officer dashboard

     [if DENIED]
     → renders <DecisionCard decision="denied" reasons=[...]/>
     "Unfortunately, we're unable to approve your loan at this time.
      Here's what you can do to improve your eligibility: ..."
```

### Phase 5: HITL (human_review node — officer side)

```
Officer opens dashboard → sees new item in queue
    → clicks into application
    → sees: AI recommendation, composite score, 4C breakdown,
            all document extractions, fraud flags, DTI ratio
    → clicks "Approve" / "Reject" / "Request More Info"

If "Request More Info":
    → officer types what's needed: "Need latest 3 months bank statement"
    → customer's chat reopens with:
       AI: "Our review team has looked at your application and needs 
            one additional document: your latest 3 months bank statement."
       → renders <DocUploadWidget type="bank_statement"/>
```

---

## 9. Backend Changes Summary

### 9.1 Remove

- `evoagentx` dependency and all EvoAgentX imports
- `src/agents/orchestrator.py` (replaced by LangGraph graph)
- `src/workflows/loan_underwriting_workflow.py` (replaced by LangGraph graph)
- `src/evolution/` (deferred to future)
- `src/memory/mem0_config.py` and `mem0ai` dependency (LangGraph checkpointer replaces this for MVP)
- Evolution-related API routes (`src/api/routes/evolution.py`)

### 9.2 Add

- `langgraph`, `langgraph-checkpoint-postgres` dependencies
- `src/graph/` — LangGraph state, nodes, tools, graph definition
- `src/auth/` — Google SSO, JWT, middleware
- `src/chat/` — SSE streaming endpoint, Vercel AI SDK adapter
- New DB models: `User`, `Conversation`, `ChatMessage`
- Alembic migrations for all schema changes

### 9.3 Modify

- `src/config.py` — add Google SSO, Azure Doc Intelligence, JWT settings
- `src/db/models.py` — new tables, Float→Numeric, cascade deletes, user_id FK
- `src/main.py` — add CORS, auth middleware, chat routes
- `src/tools/internal/*` — keep all, bind as LangGraph tools
- `src/tools/external/*` — keep all, bind as LangGraph tools
- `src/tools/internal/ocr_tool.py` — replace mock with real Azure Doc Intelligence
- `src/api/routes/hitl.py` — wire to authenticated officer, real officer_id from JWT
- `src/api/routes/applications.py` — scope to authenticated user

### 9.4 Dependencies

```
# Remove
evoagentx
mem0ai
aioredis  (redundant with redis>=5)

# Add
langgraph>=0.4.0
langgraph-checkpoint-postgres>=2.0.0
langchain-openai>=0.3.0
azure-ai-documentintelligence>=1.0.0
azure-storage-blob>=12.24.0
python-jose[cryptography]>=3.3.0  (already in requirements)
authlib>=1.4.0
nextauth  (frontend)
```

---

## 10. Infrastructure

### 10.1 Docker Compose (Dev)

Add Next.js frontend service alongside existing services:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8000
    - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
    - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
  depends_on:
    - app
```

### 10.2 Azure (Prod)

- Next.js + FastAPI both deploy to existing AKS cluster (`aks-loan-underwriting-dev`)
- Documents stored in Azure Blob (`stloanuwdocs2026`)
- PostgreSQL: existing `psql-loan-underwriting-dev`
- Redis: existing `redis-loan-underwriting-dev`
- Container images pushed to `acrloanuw2026`

### 10.3 CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 11. File Structure (New/Modified)

```
Loan_origination_Agent/
├── frontend/                          # NEW - Next.js 15 app
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # Landing + Google Sign In
│   │   ├── chat/
│   │   │   ├── page.tsx               # New conversation
│   │   │   └── [id]/page.tsx          # Resume conversation
│   │   ├── status/
│   │   │   └── page.tsx               # Application status tracker
│   │   ├── dashboard/
│   │   │   ├── page.tsx               # Officer queue
│   │   │   └── [id]/page.tsx          # Application detail review
│   │   └── api/
│   │       └── auth/
│   │           └── [...nextauth]/route.ts  # Google SSO
│   ├── components/
│   │   ├── chat/
│   │   │   ├── chat-interface.tsx
│   │   │   ├── message-bubble.tsx
│   │   │   ├── tool-renderer.tsx      # Maps tool calls → components
│   │   │   └── chat-input.tsx
│   │   ├── tools/                     # Inline UI components
│   │   │   ├── basic-info-form.tsx
│   │   │   ├── loan-details-form.tsx
│   │   │   ├── doc-upload-widget.tsx
│   │   │   ├── verification-card.tsx
│   │   │   ├── eligibility-card.tsx
│   │   │   ├── progress-tracker.tsx
│   │   │   ├── offer-card.tsx
│   │   │   ├── decision-card.tsx
│   │   │   └── score-summary.tsx
│   │   ├── dashboard/
│   │   │   ├── review-queue.tsx
│   │   │   ├── application-detail.tsx
│   │   │   └── action-bar.tsx
│   │   └── ui/                        # shadcn/ui components
│   ├── lib/
│   │   ├── auth.ts                    # NextAuth config
│   │   └── api.ts                     # API client
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── Dockerfile
├── src/                               # MODIFIED - FastAPI backend
│   ├── auth/                          # NEW
│   │   ├── __init__.py
│   │   ├── google_sso.py
│   │   ├── jwt_handler.py
│   │   └── middleware.py
│   ├── graph/                         # NEW - replaces agents/ + workflows/
│   │   ├── __init__.py
│   │   ├── state.py                   # LoanApplicationState
│   │   ├── graph.py                   # StateGraph definition
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── intake.py
│   │   │   ├── doc_collection.py
│   │   │   ├── doc_verification.py
│   │   │   ├── bureau_pull.py
│   │   │   ├── income_verification.py
│   │   │   ├── risk_assessment.py
│   │   │   ├── fraud_detection.py
│   │   │   ├── score_aggregation.py
│   │   │   ├── compliance.py
│   │   │   ├── pricing.py
│   │   │   ├── decision.py
│   │   │   ├── offer_generation.py
│   │   │   └── human_review.py
│   │   └── prompts/
│   │       ├── __init__.py
│   │       └── builder.py             # Dynamic prompt assembly
│   ├── chat/                          # NEW
│   │   ├── __init__.py
│   │   ├── stream.py                  # SSE endpoint
│   │   └── adapter.py                 # LangGraph → Vercel AI SDK format
│   ├── tools/                         # KEEP - bind as LangGraph tools
│   │   ├── internal/                  # All existing tools kept
│   │   └── external/                  # All existing clients kept
│   ├── db/
│   │   ├── models.py                  # MODIFY - add User, Conversation, ChatMessage
│   │   └── session.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── applications.py        # MODIFY - scope to auth user
│   │   │   ├── hitl.py                # MODIFY - real officer_id from JWT
│   │   │   ├── documents.py           # MODIFY - Azure Blob storage
│   │   │   └── reports.py             # KEEP
│   │   └── middleware/
│   │       └── audit.py               # KEEP
│   ├── config.py                      # MODIFY - new settings
│   └── main.py                        # MODIFY - CORS, auth, chat routes
├── alembic/
│   └── versions/
│       └── 001_initial_v4.py          # NEW - full schema migration
└── requirements.txt                   # MODIFY - swap deps
```
