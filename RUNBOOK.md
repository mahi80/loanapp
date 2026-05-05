# Loan Agent Demo — UI-Only Runbook

Driving the live loan agent at `https://loan.acpgovernance.com/` and showing governance reactions on `https://dashboard.acpgovernance.com/`. **No terminal commands** — every action is a click in the dashboard or a sentence typed at Q.

Companion to [scripts/demo_sanity_check.py](https://github.com/mahi80/rbi/blob/main/scripts/demo_sanity_check.py) (pre-flight) and [docs/how-to-use-q.md](https://github.com/mahi80/rbi/blob/main/docs/how-to-use-q.md) (operator narration script).

## Canonical identifiers

- `agent_code = LEN-LOA-01`
- `agent_name = lending-loan-processing-disbursement`
- `bu = Lending`
- Dashboard's canonical `agent_id` looks like `agent_lending_loan_processing_disbursement_<hash>` — grab it from `/agents` once at start.

---

## 1. Pages to open (left-to-right tabs, in this order)

| # | URL | What to do once it's open |
|---|-----|---------------------------|
| 1 | `/agents` | Filter **BU = Lending**, click **LEN-LOA-01** to capture the agent_id and reach the detail page |
| 2 | `/agents/{id}/monitor` | **Centerpiece — leave dominant.** 35-control grid + cost meter + tool-call traces, 10 s poll |
| 3 | `/governance-map` | Click the LEN-LOA-01 node → drawer with pause/resume/kill |
| 4 | `/cyber-risk/dashboard` | 0–100 risk score per agent, Top-10 worst (60 s + WS invalidation) |
| 5 | `/cyber-risk/detections` | Filter **status = open, severity = P1** (30 s poll) |
| 6 | `/cyber-risk/threat-intel` | The **Scan now** button lives here |
| 7 | `/activity-log` | Filter **bu = Lending** → live action ticker (10 s poll) |
| 8 | `/audit?bu=Lending` | Per-tool-call verdicts, last 24 h |
| 9 | `/controls` | Where you flip Q1–Q35 live |

The Q mascot panel floats over every page — keep it expanded on the Watch tab in a corner.

---

## 2. Q chat queries to type (mascot panel → Chat tab)

Q is on Groq-first with Ollama fallback. Several intents are deterministic (no SLM call) so they answer instantly.

1. `Show me the status of the loan agent`
2. `What's the current cyber risk for the Lending BU?`
3. `Show me threat intel from the last 7 days` *(deterministic — sorted by date within severity)*
4. `Are there any open P1 incidents?`
5. `Show me the audit log for LEN-LOA-01`
6. `Why did Q11 fire on the loan agent?` *(only if it has — otherwise pick a control that did)*
7. `Run a threat-impact scan now`
8. `Which agents have budget overruns this week?`
9. `Have we seen this pattern before?` *(semantic memory recall)*
10. `What is RBI Recommendation 14?` *(definitional — proves Q knows the regs without an SLM call)*
11. `Pause the loan agent` *(Q proposes the action; you confirm in the deep-link drawer)*
12. `Generate the RBI quarterly report`

The Watch tab will pop new alert bubbles as activity fires from §3 and §4.

---

## 3. Filters / dropdowns to set on the way

- `/agents` → BU = **Lending**
- `/audit` → BU = **Lending**, last **24 h**
- `/cyber-risk/detections` → severity = **P1**, status = **open**
- `/drift` → agent = **LEN-LOA-01**
- `/compliance` → framework = **RBI FREE-AI**
- `/reports` → framework = **RBI FREE-AI**, format = **PDF**

---

## 4. Buttons to click for live changes (least → most dramatic)

| Where | Button | What the audience sees |
|-------|--------|------------------------|
| `/cyber-risk/threat-intel` | **Scan now** | Cross-references LEN-LOA-01 against advisories; matches pop in Q's Watch tab within seconds |
| `/controls` (Lending row) | Toggle **Q11** OFF | Q narrates the flip into Watch; effective on the next tool call (no restart) |
| `/controls` (Lending row) | Toggle **Q11** back ON | Same Watch narration; `RELAX_CONTROL` audit row written |
| `/agents/{id}/monitor` | **Pause** → confirm modal | Red banner appears within 10 s; heartbeat starts returning 423 Locked |
| `/agents/{id}/monitor` | **Resume** | Banner clears within 10 s |
| `/mcp-trust` | **Approve** on a pending row | Agent's tool calls to that MCP server resume on next heartbeat |
| `/onboard-agent` | Submit a fake agent in a BU with no AI policy | Q's right-rail blocks with **NO_POLICY_EXISTS** (RBI Rec 14 hard prereq) |
| `/ai-policy` | **Approve** a draft policy → status flips to `board_approved` | Unlocks onboarding for that BU |
| `/notifications` | **Send test alert** | Slack/Teams/email lights up *(verify before stage — v60.x smoke not re-run)* |
| `/reports` | **Generate** RBI report → wait → **Download** | Signed PDF with chain-of-custody hash you can hand a regulator |
| `/notifications` (Org tab) | Toggle **Lending BU active = OFF** | Confirm modal appears (PR #67) — warns "running agents in this BU" |
| `/governance-map` | Click LEN-LOA-01 node → drawer → **Kill** | Agent terminates on next heartbeat — only do this if you can cleanly re-onboard |

⚠️ **Sacred-set guard**: Q25 / Q29 / Q28 / Q13 (and Q14 on financial BUs) cannot be silently disabled. Direct toggle still works for CIO override but writes a `RELAX_CONTROL` audit row. For the demo, prefer Q11, Q1, or Q3 — visible effects, no guard tripped.

---

## 5. Suggested storyline (12–15 minutes)

1. **Open** `/agents` → filter Lending → click LEN-LOA-01 → land on `/agents/{id}/monitor`
2. **Narrate** the 35-control grid + climbing cost meter + scrolling tool-call feed (already live)
3. **Ask Q** queries 1, 2, 3 — status, risk, threat intel
4. **Click** `/cyber-risk/threat-intel` → **Scan now** → watch Watch tab pop alerts
5. **Toggle** Q11 OFF on `/controls` → show Watch narration → toggle ON again
6. **Pause** the agent on the monitor banner → red banner appears → **Resume**
7. **Open** `/onboard-agent` → submit a fake agent in a no-policy BU → Rec 14 hard-block
8. **Open** `/ai-policy` → show a board-approved policy → unlock the BU
9. **Click** `/reports` → Generate RBI report → Download signed PDF
10. **Wrap** on `/governance-map` showing the whole agent graph + sub-agents

---

## 6. Things to pre-empt

- **Loan stack might be cold** — no restart policy on the loan compose, so any crash or reboot leaves it down. Run [scripts/demo_sanity_check.py](https://github.com/mahi80/rbi/blob/main/scripts/demo_sanity_check.py) 30 minutes before stage. If it fails — or if `/dashboard` shows "This page couldn't load" / 502 — follow §7 below to diagnose and recover.
- **`ACP_THREAT_AUTO_PAUSE` is OFF in prod** — manual scan finds matches but won't auto-pause unless you flipped the flag and redeployed (`acp-deploy.sh`, not `docker restart`)
- **`/review-queue` is empty by design** — Q12 active-learning is off for the loan agent. Don't open this tab unless you want to explain why
- **Notification send-test** — schema/dispatcher exist, but real Slack smoke hasn't been re-run for v60.x. Click **Send test alert** during pre-flight, not on stage
- **agent_id vs agent_code** — every audit/alert/cost row is keyed by the canonical `agent_id`, not `LEN-LOA-01`. If you query/filter by code in any custom view you'll get 0 rows
- **The loan agent calls a real LLM** — repeated runs accumulate real cost. Keep an eye on `/cost` if you fire many submissions

---

## 7. Troubleshooting: loan stack down or `/dashboard` returning 502

The loan compose has no `restart: unless-stopped`, so any container exit leaves the stack down until somebody runs it back up. If `https://loan.acpgovernance.com/` or `/dashboard` shows "This page couldn't load" / 502, follow this in order.

### Diagnose first (don't just `up -d` blindly)

```bash
ssh azureuser@20.219.134.205
cd ~/loan-agent/Loan-origination-Agents
docker compose ps              # which services + state (Up / Exit N)
docker compose logs --tail 80  # why the failing service died
```

Read the exit code:
- **`Exit (137)`** — OOM-killed. vm-mirofish is `Standard_B4ms` (16 GB) and shared with the dashboard. Bring up only the loan service first, watch `docker stats`.
- **`Exit (1)`** — app crash. The logs above will have the traceback. Common cause: a missing env var or an upstream LLM key that rotated.
- **`Exit (0)`** — clean exit (someone stopped it). Just `up -d`.

### Bring it back

```bash
docker compose up -d
curl -I https://loan.acpgovernance.com            # expect 200
curl -I https://loan.acpgovernance.com/dashboard  # expect 200
```

### If the root works but `/dashboard` still 502s

That's an nginx/upstream mismatch — the loan-app is up but nginx is pointing the `/dashboard` location at a port that didn't come back. Check:

```bash
sudo cat /etc/nginx/sites-enabled/* | grep -A 30 'loan.acpgovernance.com'
docker compose config | grep -E 'ports|services:' -A 1
```

If the published port differs from what nginx expects, fix the compose ports back to the original or update the nginx upstream + reload (`sudo nginx -s reload`).

### Make this the last cold-stack incident (one-time fix)

Once the stack is healthy, edit `~/loan-agent/Loan-origination-Agents/docker-compose.yml` and add `restart: unless-stopped` under each service, then `docker compose up -d`. After that the stack survives reboots and crashes — see [README.md L652](https://github.com/mahi80/rbi/blob/main/README.md#L652).

---

## 8. Cleanup (also UI)

- `/agents/{id}/monitor` → **Resume** if you paused
- `/controls` → toggle any Q-control you flipped back to its original state
- `/onboarding-approvals` → reject the fake onboarding request you submitted in step 7 of the storyline
- `/notifications` (Org tab) → re-enable Lending if you toggled it off
