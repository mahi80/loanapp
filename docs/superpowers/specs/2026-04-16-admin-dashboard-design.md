# Admin Dashboard — Officer Command Center

**Date:** 2026-04-16
**Branch:** `feature/admin-dashboard`
**Purpose:** Premium officer dashboard for bank CTO demo — full KPIs, review queue, 4-tab settings, analytics, customer HITL notifications.
**Mockup:** `.superpowers/brainstorm/13529-1776350579/content/admin-final.html`

---

## 1. Architecture

Single-page client component at `/dashboard` with 4 client-side tabs (no sub-routes). All data fetched via authenticated API calls with `officer` role guard.

```
/dashboard (layout.tsx — server: auth check + redirect)
  └── page.tsx ("use client" — full dashboard SPA)
       ├── OfficerTopbar (logo, 4 tab nav, clock, bell, avatar)
       ├── DashboardTab (KPIs, recent apps, agent pipeline)
       ├── ReviewTab (queue table, detail modal/expand)
       ├── SettingsTab (4 sub-tabs: docs, rates, rules, agents)
       └── AnalyticsTab (charts, audit trail)
```

**Approach:** Option A — single page, client-side tab switching. Tab switch re-triggers staggered `fadeUp` animations. No page navigations within the dashboard.

**Review detail:** When officer clicks "Review" on a queue item, it opens an inline expanded detail view (not a separate route). The current `/dashboard/[id]` route is replaced by inline expansion within the Review tab.

---

## 2. Design System (Locked In)

### Colors
| Token | Value | Usage |
|---|---|---|
| `--bg` | `#E8E2D6` | Page background (warm parchment) |
| `--card` | `#FFFDF8` | Card backgrounds (warm white) |
| `--card-alt` | `#F5F2EA` | Secondary card backgrounds |
| `--navy` | `#0C1222` | Primary dark, active nav, buttons |
| `--navy-mid` | `#1A2332` | Button hover states |
| `--gold` | `#C8A24E` | Accent, AI confidence card, shimmer |
| `--gold-light` | `#E8D5A0` | Gold hover state |
| `--gold-glow` | `rgba(200,162,78,0.15)` | Navy card radial glow |
| `--text` | `#0C1222` | Primary text |
| `--text-sec` | `#7A7568` | Secondary text |
| `--text-muted` | `#B0A999` | Muted labels |
| `--border` | `rgba(12,18,34,0.06)` | Card borders |
| `--green` | `#2E8B57` | Approved, positive |
| `--red` | `#C0392B` | Denied, alerts |
| `--amber` | `#D4860B` | Escalated, warnings |
| `--blue` | `#3B7DDD` | Conditional, info |

### Typography
| Font | Weight | Usage |
|---|---|---|
| DM Serif Display | 400 | Headings, KPI numbers, section titles |
| DM Sans | 400/500/600/700 | Body text, labels, buttons |
| JetBrains Mono | 500 | Data values, reference numbers, clock |

Load via `next/font/google` (not CDN link) to avoid FOUT.

### Shadows
- `--sh`: `0 1px 2px rgba(12,18,34,0.04), 0 4px 16px rgba(12,18,34,0.03)` (default)
- `--sh-h`: `0 4px 20px rgba(12,18,34,0.07), 0 1px 3px rgba(12,18,34,0.04)` (hover)

### Border Radius
- Cards: `16px`
- Topbar: `18px`
- Buttons: `10px`
- Badges: `20px`
- Avatars/icons: `12px`

---

## 3. Component Inventory

### 3.1 OfficerTopbar

Sticky topbar with 12px margin from edges, 64px height, rounded 18px corners, backdrop blur.

**Elements:**
- **Logo:** Navy square (36px, rounded 10px) with Lucide `landmark` icon in gold + "LoanAI" in DM Serif Display 18px
- **Nav:** Pill-style tabs in card-alt background, 4px padding, 12px border-radius container
  - Dashboard (layout-dashboard icon)
  - Review (clipboard-check icon) + **red pulsing badge** with live count from `GET /api/v1/admin/stats`
  - Settings (sliders-horizontal icon)
  - Analytics (bar-chart-3 icon)
  - Active tab: navy background, white text, shadow
- **Right side:**
  - Live clock (JetBrains Mono 12px, updates every second)
  - Settings gear button (38px square, 12px radius)
  - Bell button with red dot indicator (7px, absolute positioned)
  - Avatar: 38px square, 12px radius, gold gradient background, initials in white 13px bold

**Backdrop:** `backdrop-filter: blur(20px)` on the topbar for glass effect.

**Animation:** `slideDown` — 0.5s cubic-bezier(0.16,1,0.3,1), translates from -20px.

### 3.2 Dashboard Tab

12-column CSS grid with 12px gaps. Cards animate in with staggered `fadeUp` (60ms delay per card).

**Tab switch animation re-trigger:** Use `key={activeTab}` on the tab content wrapper to force React remount, which re-triggers all CSS entry animations.

#### Row 1: KPI Cards (3 cards spanning 4+5+3 columns)

**Card 1: Total Applications (span 4)**
- Standard card style
- Label: "Total Applications" with file-text icon
- Value: DM Serif Display 44px, letter-spacing -2px
- Trend indicators: green up arrows for "This week" and "This month" with percentages
- "View All" navy button at bottom — switches to Review tab on click
- **Data:** `GET /api/v1/admin/stats` → `total_applications`, `weekly_change_pct`, `monthly_change_pct`

**Card 2: Decision Breakdown (span 5)**
- 4 vertical bars (Approved green, Denied red, Escalated amber, Conditional blue)
- Each bar: gradient fill, percentage label above, category label below
- Bar heights proportional to percentage
- Month label top-right
- **Animation:** `barGrow` from scaleY(0) to scaleY(1), staggered 100ms per bar
- **Data:** `GET /api/v1/admin/stats` → `decision_breakdown: {approved: N, denied: N, escalated: N, conditional: N}`

**Card 3: AI Confidence (span 3, gold gradient)**
- Special card: gold gradient background (#C8A24E → #A07828)
- Cross-hatch SVG pattern overlay at 6% opacity
- SVG donut chart (130px, stroke-width 10, navy stroke)
- Center: DM Serif Display percentage + "accuracy" subtitle
- Footer: "X% officer override rate"
- **Animation:** `ringFill` — stroke-dashoffset animates from full to computed value over 1.2s
- **Animation:** `shimmer` — linear gradient sweep every 3s
- **Data:** `GET /api/v1/admin/stats` → `ai_confidence_pct`, `override_rate_pct`

#### Row 2: KPI Cards (3 cards spanning 3+3+6 columns) — BUT mockup shows 3+3+6 as navy+alert+recent

**Card 4: Avg Processing Time (span 3, navy background)**
- Dark navy card with radial gold glow in top-right
- Label: "Avg Processing" with timer icon (gold text)
- Value: DM Serif Display 52px + "h" suffix in DM Sans 20px
- Trend: gold text "22% faster" with trending-down icon
- **Data:** `GET /api/v1/admin/stats` → `avg_processing_hours`, `processing_change_pct`

**Card 5: Pending Reviews (span 3, amber alert)**
- Alert card: warm gradient background (#FEF7E6 → #FFF2D6), amber border
- Alert triangle icon (28px, amber)
- "3 Pending" in DM Serif Display 22px amber
- "Applications awaiting review" subtitle
- "Oldest: 6h 23m ago" in JetBrains Mono 11px amber
- "Review Now" button (amber background, white text) — switches to Review tab on click
- **Data:** `GET /api/v1/admin/stats` → `pending_review_count`, `oldest_pending_minutes`

**Card 6: Recent Applications (span 6)**
- Section header: "Recent Applications" (DM Serif Display 17px) + "Latest loan submissions" subtitle + "View all" pill button
- 4 application rows, each with:
  - Avatar: 42px square, 12px radius, colored background based on status (green=approved, amber=review, red=denied, blue=conditional), initials
  - Name (14px, 600 weight)
  - Subtitle: reference number + loan type + time ago (JetBrains Mono 11px, muted)
  - Amount: DM Serif Display 16px with ₹ Indian formatting (lakh system: `₹5,00,000` not `₹500,000`). Use `Intl.NumberFormat('en-IN')`.
  - Status badge (colored pill: b-g/b-r/b-a/b-b)
  - Avatar color mapping: approved → green `#E8F5EE/#1B6B3A`, escalated/review → amber `#FDF3E2/#8B5E00`, denied → red `#FCEAEA/#922020`, conditional → blue `#E8F0FE/#1A56B8`
  - Initials: first letter of first name + first letter of last name (e.g., "Raj Kumar" → "RK")
  - Chevron-right arrow button (32px, 8px radius)
- Hover: row indents 4px, avatar scales 1.06
- **Data:** `GET /api/v1/admin/recent-applications?limit=4`

#### Row 3: Agent Pipeline (span 12)

- Section header: "Agent Pipeline" + "13 AI agents processing each application" + "Configure" pill button (links to Settings > Agents tab)
- Horizontal scrollable pipeline: 8 visible nodes with → arrows between
- Each node (110px min-width, 14px padding, card-alt background, 14px radius):
  - Lucide icon (22px, centered)
  - Name (11px, 600 weight)
  - Latency (JetBrains Mono 16px)
  - Success rate or HITL % (10px, 600 weight, colored: green if >97%, amber if 95-97%, red if <95%)
- Active node (Decision): navy background, white text, gold rate text
- **Animation:** `nodeIn` — staggered 50ms per node, translateY(10px) + scale(0.95) → normal
- **Data:** Hardcoded for demo (the 8 visible pipeline stages with realistic latency/accuracy numbers). Can optionally aggregate from AgentOutput table later.

Nodes shown: Intake → Docs → Verify → Bureau → Income → Risk → Pricing → Decision

### 3.3 Review Queue Tab

Header: "Review Queue" (DM Serif Display 24px) + "Applications escalated by AI for human decision" subtitle.

**Table (full width card):**
| Column | Font/Style | Source |
|---|---|---|
| Applicant | Avatar (34px, initials, colored bg) + name (600 weight) | Application.applicant_name |
| Reference | JetBrains Mono 12px | Application.reference_number |
| Amount | DM Serif Display | Application.loan_amount (₹ formatted) |
| AI Score | JetBrains Mono 600 weight | CreditScore.composite_score |
| Risk Flags | Colored badge pills (b-a amber, b-r red) | CreditDecision.conditions or derived from score/DTI |
| Waiting | JetBrains Mono 12px, amber if >2h | Computed from CreditDecision.decided_at |
| Action | "Review" navy button with eye icon | Opens inline detail view |

**Table styles:**
- Header: 10px uppercase, 1px letter-spacing, muted color, bottom border
- Rows: 14px padding, bottom border, hover background card-alt
- Last row: no bottom border

**Inline Detail View (replaces `/dashboard/[id]` route):**
When officer clicks "Review", the table row expands or a panel slides in below showing:
- Application data card (name, amount, type, status)
- AI Recommendation card (decision badge, risk flags)
- Agent Outputs (collapsible panels per agent)
- Action bar at bottom: Approve (green) / Deny (red) / Conditional (blue) buttons + notes textarea

Uses existing `GET /api/v1/hitl/{id}` and `POST /api/v1/hitl/{id}/review` APIs.

**HITL Queue API Enhancement Required:**
The current `GET /api/v1/hitl/queue` returns hardcoded `"Borderline risk score - requires human review"` for every escalation. Must be enhanced to return:
- `composite_score` from `CreditScore` table
- `risk_flags` array derived from: DTI ratio > 0.50 → "Borderline DTI", composite_score < 600 → "Low score", loan_amount > 10L → "High amt", bureau enquiry_count < 3 → "Thin file", income volatility > 0.3 → "Income volatility"
- `waiting_since` timestamp (from `CreditDecision.decided_at` or `Application.created_at`)
- `applicant_name` and `reference_number` directly (not just application_id)

### 3.4 Settings Tab

Header: "Settings" (DM Serif Display 24px) + subtitle. Right-aligned sub-tabs.

**Level 1 tabs:** Document Rules | Rate Cards | Product Rules | Agents
**Level 2 tabs (Document Rules only):** Personal Loan | Home Loan | Auto Loan | Business

Tab style: pill container (card-alt background, 4px padding, 12px radius), active tab has card background + shadow.

#### 3.4.1 Document Rules Sub-Tab

3-column grid (each span 4):

**Column 1: All Applicants** (user icon, gold)
- "Required regardless of employment"
- Documents:
  - PAN Card — Tax ID verification — MANDATORY — toggle ON
  - Aadhaar Card — KYC identity proof — MANDATORY — toggle ON
  - Applicant Photo — Face match verification — MANDATORY — toggle ON
  - Bank Statement — 6 months, income & cash flow — MANDATORY — toggle ON
  - Address Proof — If different from Aadhaar — OPTIONAL — toggle ON

**Column 2: Salaried** (briefcase icon, gold)
- "Additional for salaried employees"
- Documents:
  - Payslips (3 months) — Salary verification — MANDATORY — toggle ON
  - Form 16 — TDS confirmation — RECOMMENDED — toggle ON
  - Employment Letter — Employer verification — RECOMMENDED — toggle ON
  - Salary Certificate — Government employees — OPTIONAL — toggle OFF

**Column 3: Self-Employed** (store icon, gold)
- "Additional for business owners"
- Documents:
  - ITR (2 years) — Income declaration — MANDATORY — toggle ON
  - GST Certificate — Business legitimacy — RECOMMENDED — toggle ON
  - Business Registration — Udyam / Shop license — RECOMMENDED — toggle ON
  - P&L Statement — Business financials — OPTIONAL — toggle OFF
  - Balance Sheet — Audited net worth — OPTIONAL — toggle OFF

**Tier badges:**
- MANDATORY: red background (#FCEAEA), dark red text (#922020)
- RECOMMENDED: amber background (#FDF3E2), dark amber text (#8B5E00)
- OPTIONAL: green background (#E8F5EE), dark green text (#1B6B3A)

**Toggle switches:** 38px wide, 22px tall, 11px border-radius, 18px knob. ON = green, OFF = #D0CABE. Animated slide (0.3s cubic-bezier).

**Footer bar (span 12):** Navy background, 16px radius.
- Left: info icon + "Changes apply to the AI agent immediately for new conversations."
- Right: "Save & Update Agent" gold button
- On save: POST to API, success toast

**Data flow:**
- Load: `GET /api/v1/config/document-requirements?loan_type=personal`
- Save: `POST /api/v1/config/document-requirements` with full config
- Agent: `doc_collection_node` reads from DB `product_rules` table at runtime

#### 3.4.2 Rate Cards Sub-Tab

Display active rate cards grouped by loan type → risk category.

Table per loan type:
| Risk Category | Score Range | Interest Rate | Processing Fee % | Insurance % | Actions |
|---|---|---|---|---|---|
| Low | 700-900 | 10.5% | 1.5% | 0.5% | Edit |
| Medium | 600-699 | 13.0% | 2.0% | 0.75% | Edit |
| High | 450-599 | 16.5% | 2.5% | 1.0% | Edit |
| Very High | 300-449 | — | — | — | Denied |

Edit: inline editing with save button. Uses existing `PUT /api/v1/config/rate-cards/{id}`.

#### 3.4.3 Product Rules Sub-Tab

Display eligibility rules per loan type.

Editable fields per rule:
- Min Age / Max Age
- Min Monthly Income
- Max Loan-to-Income Multiplier
- Any custom rules from `rule_config` JSONB

Uses existing `GET/PUT /api/v1/config/product-rules` APIs.

#### 3.4.4 Agents Sub-Tab

List all 13 agent nodes with:
- Name and icon
- Current status: enabled/disabled toggle
- Avg latency (from AgentOutput or hardcoded demo values)
- Success rate
- Description (from prompts/builder.py)

For demo: hardcoded agent list with realistic stats. Toggle is visual but doesn't affect the graph (graph always runs all 13 nodes). Can note "coming soon" for actual agent enable/disable.

### 3.5 Analytics Tab

Header: "Analytics" (DM Serif Display 24px) + "Performance insights and decision audit trail" subtitle.

**Row 1: Two chart cards (span 6 each, 260px height)**

**Approval Trends (left):**
- Line/bar chart showing weekly approved/denied/escalated counts over last 8 weeks
- Use `recharts` (already common in Next.js projects) with the design system colors
- **Data:** `GET /api/v1/admin/analytics/trends?weeks=8`

**Risk Distribution (right):**
- Horizontal bar chart showing score distribution buckets (300-449, 450-599, 600-699, 700-900)
- Color-coded by risk category
- **Data:** `GET /api/v1/admin/analytics/risk-distribution`

**Row 2: Decision Audit Trail (span 12, 200px min height)**

Table showing recent decisions:
| Date | Applicant | AI Decision | Officer Decision | Override? | Confidence | Notes |
|---|---|---|---|---|---|---|

- Highlights overrides in amber
- **Data:** `GET /api/v1/admin/analytics/audit-trail?limit=20`

---

## 4. Backend APIs

### 4.1 New Endpoints

All require `officer` role auth.

#### `GET /api/v1/admin/stats`
Returns dashboard KPI data.
```json
{
  "total_applications": 247,
  "weekly_change_pct": 1.3,
  "monthly_change_pct": 12.2,
  "decision_breakdown": {
    "approved": 168, "denied": 52, "escalated": 17, "conditional": 10
  },
  "ai_confidence_pct": 87.4,
  "override_rate_pct": 4.1,
  "avg_processing_hours": 4.2,
  "processing_change_pct": -22.0,
  "pending_review_count": 3,
  "oldest_pending_minutes": 383
}
```

Queries: `Application` count + `CreditDecision` aggregate by decision type + `HITLReview` count for overrides + timestamp diffs.

#### `GET /api/v1/admin/recent-applications?limit=4`
```json
[{
  "id": "uuid",
  "applicant_name": "Raj Kumar",
  "reference_number": "LN-A8F2C4D1",
  "loan_type": "personal",
  "loan_amount": 500000,
  "status": "decided",
  "decision": "approved",
  "created_at": "2026-04-16T14:30:00Z"
}]
```

#### `GET /api/v1/config/document-requirements?loan_type=personal`
```json
{
  "loan_type": "personal",
  "groups": [
    {
      "group": "all",
      "label": "All Applicants",
      "icon": "user",
      "description": "Required regardless of employment",
      "documents": [
        {"name": "PAN Card", "key": "pan_card", "description": "Tax ID verification", "tier": "mandatory", "enabled": true},
        {"name": "Aadhaar Card", "key": "aadhaar", "description": "KYC identity proof", "tier": "mandatory", "enabled": true}
      ]
    },
    {"group": "salaried", ...},
    {"group": "self_employed", ...}
  ]
}
```

#### `POST /api/v1/config/document-requirements`
Accepts same structure, writes to `product_rules` table with `rule_name="document_requirements"` and `rule_config` containing the full config per loan type.

#### `GET /api/v1/admin/analytics/trends?weeks=8`
```json
{
  "weeks": [
    {"week": "2026-W11", "approved": 42, "denied": 12, "escalated": 3, "conditional": 2}
  ]
}
```

#### `GET /api/v1/admin/analytics/risk-distribution`
```json
{
  "buckets": [
    {"range": "700-900", "category": "low", "count": 89},
    {"range": "600-699", "category": "medium", "count": 67}
  ]
}
```

#### `GET /api/v1/admin/analytics/audit-trail?limit=20`
```json
[{
  "application_id": "uuid",
  "applicant_name": "Priya Sharma",
  "ai_decision": "escalated",
  "officer_decision": "approved",
  "is_override": true,
  "confidence": 0.62,
  "notes": "Strong employer, borderline DTI acceptable",
  "decided_at": "2026-04-16T12:00:00Z"
}]
```

### 4.2 Modified Endpoints

- Add `officer` role auth to `GET/PUT /api/v1/config/rate-cards` and `GET/PUT /api/v1/config/product-rules`

### 4.3 Agent Modification

**`src/graph/nodes/doc_collection.py`** — replace hardcoded document list:

```python
# BEFORE (hardcoded)
required = ["pan_card", "aadhaar", "selfie", "bank_statement"]

# AFTER (reads from DB)
from src.db.session import async_session_factory
from src.db.models import ProductRule, LoanType

async with async_session_factory() as session:
    result = await session.execute(
        select(ProductRule).where(
            ProductRule.product_type == LoanType(loan_type),
            ProductRule.rule_name == "document_requirements",
            ProductRule.active == True,
        )
    )
    rule = result.scalar_one_or_none()
    if rule and rule.rule_config:
        # Parse config to get enabled mandatory+recommended docs
        required = [doc["key"] for group in rule.rule_config.get("groups", [])
                    for doc in group.get("documents", [])
                    if doc.get("enabled") and doc.get("tier") in ("mandatory", "recommended")]
    else:
        # Fallback to defaults
        required = ["pan_card", "aadhaar", "selfie", "bank_statement"]
```

---

## 5. Customer-Side HITL Notification

### What already works
- Officer submits review → `hitl.py` injects `ChatMessage` into conversation
- Customer reopens chat → sees the decision message

### What to add
- **Status page enhancement:** When `Application.status == "decided"`, show a decision banner at top of the status detail page with the officer's decision (approved/denied/conditional) and a link back to chat
- **Chat page:** If customer returns to `/chat/[id]`, the auto-loaded message history includes the injected decision message — no extra work needed, already works via `GET /conversations/{id}/messages`

---

## 6. Animations (CSS + Framer Motion)

Use **CSS animations** for the static effects (matching the mockup exactly) and **Framer Motion** only for tab switch transitions.

| Animation | Trigger | Implementation |
|---|---|---|
| `slideDown` | Page load | CSS on topbar |
| `fadeUp` | Tab switch | CSS, re-triggered by key change on tab content wrapper |
| `barGrow` | Dashboard tab visible | CSS with animation-delay per bar |
| `ringFill` | Dashboard tab visible | CSS on SVG stroke-dashoffset |
| `nodeIn` | Dashboard tab visible | CSS with staggered delay |
| `pulse` | Always (review badge) | CSS infinite animation |
| `shimmer` | Always (gold card) | CSS infinite animation |
| Grain overlay | Always | CSS `body::before` with SVG noise texture |
| Hover lifts | Hover | CSS transitions (translateY, scale, shadow) |

---

## 7. File Structure

```
frontend/src/
  app/dashboard/
    layout.tsx          — server: auth check, redirect if not logged in
    page.tsx            — "use client", main dashboard SPA
  components/officer/
    officer-topbar.tsx  — sticky topbar with nav tabs
    dashboard-tab.tsx   — KPIs, recent apps, pipeline
    review-tab.tsx      — queue table + inline detail
    review-detail.tsx   — expanded review with action buttons
    settings-tab.tsx    — 4 sub-tabs container
    doc-rules-panel.tsx — document requirements editor
    rate-cards-panel.tsx — rate card editor
    product-rules-panel.tsx — product rules editor
    agents-panel.tsx    — agent list with toggles
    analytics-tab.tsx   — charts + audit trail
    kpi-card.tsx        — reusable KPI card (standard/navy/gold/alert variants)
    pipeline-viz.tsx    — agent pipeline horizontal visualization
    stat-bar-chart.tsx  — decision breakdown bars
    donut-chart.tsx     — SVG donut for AI confidence

src/api/routes/
    admin.py            — new: stats, recent-applications, analytics endpoints
    config.py           — modified: add auth, add document-requirements endpoints
```

---

## 8. Seed Data

For the bank demo, seed the database with realistic data.
Seed script: `src/db/seed.py` — run via `python -m src.db.seed`

### 8.1 Applications (15-20)
- Mix of statuses: 8 decided (5 approved, 2 denied, 1 conditional), 3 escalated (in review queue), 4 processing, 3 leads
- Realistic Indian names, PAN numbers, loan amounts (₹1L–₹50L)
- Spread across loan types (10 personal, 3 home, 3 auto, 2 business)

### 8.2 Credit Decisions + Scores
- CreditDecision for each decided/escalated app with varied confidence (0.55–0.95)
- CreditScore for each with composite_score (380–850), DTI ratios, risk categories
- Escalated apps should have borderline scores (450–650) with specific risk flags

### 8.3 HITL Reviews (2)
- 1 override: AI escalated → officer approved (shows override in audit trail)
- 1 agreement: AI escalated → officer denied (agreement case)

### 8.4 Rate Cards (4 loan types × 4 risk categories = 16 rows)

| Loan Type | Low (700-900) | Medium (600-699) | High (450-599) | Very High (300-449) |
|---|---|---|---|---|
| Personal | 10.5% / 1.5% / 0.5% | 13.0% / 2.0% / 0.75% | 16.5% / 2.5% / 1.0% | Denied |
| Home | 8.5% / 0.5% / 0.25% | 9.5% / 0.75% / 0.4% | 11.0% / 1.0% / 0.5% | Denied |
| Auto | 9.0% / 1.0% / 0.5% | 11.5% / 1.5% / 0.6% | 14.0% / 2.0% / 0.8% | Denied |
| Business | 12.0% / 2.0% / 0.5% | 14.5% / 2.5% / 0.75% | 17.5% / 3.0% / 1.0% | Denied |

Format: interest_rate / processing_fee_pct / insurance_pct

### 8.5 Product Rules (eligibility per loan type)

| Loan Type | Min Age | Max Age | Min Income | Max Multiplier |
|---|---|---|---|---|
| Personal | 21 | 58 | ₹15,000 | 60x |
| Home | 23 | 60 | ₹25,000 | 200x |
| Auto | 21 | 60 | ₹20,000 | 48x |
| Business | 25 | 65 | ₹30,000 | 100x |

### 8.6 Document Requirements (all 4 loan types)

**Personal Loan:** (matches the mockup exactly — see Section 3.4.1)

**Home Loan:**
- All: PAN, Aadhaar, Photo, Bank Statement (6mo), Address Proof
- Salaried: Payslips (6mo) MANDATORY, Form 16 MANDATORY, Employment Letter RECOMMENDED
- Self-Employed: ITR (3yr) MANDATORY, GST Certificate MANDATORY, Business Registration RECOMMENDED, P&L RECOMMENDED, Balance Sheet RECOMMENDED
- Additional: Property Documents MANDATORY, Sale Agreement MANDATORY, Property Valuation RECOMMENDED

**Auto Loan:**
- All: PAN, Aadhaar, Photo, Bank Statement (6mo), Address Proof
- Salaried: Payslips (3mo) MANDATORY, Form 16 RECOMMENDED
- Self-Employed: ITR (2yr) MANDATORY, GST Certificate RECOMMENDED
- Additional: Quotation/Proforma Invoice MANDATORY, Existing Vehicle RC (if trade-in) OPTIONAL

**Business Loan:**
- All: PAN, Aadhaar, Photo, Bank Statement (12mo) MANDATORY, Address Proof
- Additional: ITR (3yr) MANDATORY, GST Certificate MANDATORY, Business Registration MANDATORY, P&L (2yr) MANDATORY, Balance Sheet (2yr) MANDATORY, Partnership Deed/MOA RECOMMENDED, Office Proof RECOMMENDED

### 8.7 Users (2)
- 1 customer user (for demo application data ownership)
- 1 officer user (for dashboard access)

---

## 9. Integration Checklist

Items that must happen alongside the main build to avoid gaps:

- [ ] Register `admin_router` in `src/main.py` (`app.include_router(admin_router)`)
- [ ] Add `recharts` to `frontend/package.json` dependencies
- [ ] Load DM Serif Display, DM Sans, JetBrains Mono via `next/font/google` in `frontend/src/app/dashboard/layout.tsx`
- [ ] Delete or redirect `frontend/src/app/dashboard/[id]/page.tsx` (replaced by inline review detail)
- [ ] Ensure `loan_type` is populated in `LoanApplicationState` before `doc_collection` phase (set during intake from form data)
- [ ] Enhance `GET /api/v1/hitl/queue` to return composite_score, risk_flags array, waiting_since, applicant_name, reference_number
- [ ] Add officer auth to existing config endpoints (`rate-cards`, `product-rules`)
- [ ] Add Indian ₹ lakh formatting utility: `new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })`
- [ ] Customer status detail page: add decision banner when `Application.status == "decided"` showing approved/denied/conditional with link to chat
- [ ] Grain overlay: add SVG noise texture as `::before` pseudo-element on dashboard body wrapper (not on global body to avoid affecting other pages)

---

## 10. Out of Scope

- Real-time WebSocket notifications (polling is sufficient for demo)
- Mobile responsive layout (desktop demo only)
- Agent enable/disable actually affecting the graph (visual toggle only)
- PII encryption at rest
- Alembic migrations (continue using `create_all()`)
