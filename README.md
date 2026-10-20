# Loan origination Agents 

## Governance (ACP)

The underwriting graph runs under the [ACP](https://github.com/mahi80/rbi) governance SDK
(acp-sdk 0.8.1, pinned by commit in `requirements-governance.txt`) as agent **LEN-LOA-01** in BU
**Lending**. `src/graph/governance.py` wraps the compiled graph with `acp.govern()`; it is a
no-op unless `ACP_DASHBOARD_URL` is set, so local development and the test suite are unchanged.

| Variable | Default | Meaning |
|---|---|---|
| `ACP_DASHBOARD_URL` | — | enables governance, e.g. `https://dashboard.acpgovernance.com` |
| `ACP_API_KEY` | — | dashboard agent API key |
| `ACP_AGENT_CODE` | `LEN-LOA-01` | must match the agent onboarded in the dashboard |
| `ACP_AGENT_NAME` | `lending-loan-processing-disbursement` | display name |
| `ACP_BU` | `Lending` | business unit |
| `ACP_BUDGET` | `5.0` | USD per task (Q11 cost gate) |
| `ACP_TIER` | `TIER_2` | autonomy tier (Q6) |
| `ACP_GOVERN` | `1` | set `0` to force the wrap off |

What the SDK does on first graph build: registers (idempotent, attaches to the onboarded row),
pulls the governance config set in the dashboard wizard, starts the 10 s heartbeat, and wraps
every node with the pre/post checks. A dashboard pause (manual, or Q's automatic pause on a
rogue verdict) returns `423` on the heartbeat and every node call raises `ACP-150` until the
agent is unpaused. Q37 (acp-sdk ≥ 0.8.0) blocks any tool argument that targets cloud-metadata
or link-local addresses and, from 0.8.1, every block lands in the dashboard audit log as
`allowed=false` so the `infra_attack` detector can pause the agent.

**Building the image.** `acp-sdk` is installed from the private `mahi80/rbi` repo, so the
Docker build needs a GitHub PAT with read access, passed as a BuildKit secret (never baked
into a layer):

```bash
echo ghp_xxx > .github_token          # git-ignored
DOCKER_BUILDKIT=1 docker compose build app
```

Without the token the build still succeeds but **ungoverned** (the Dockerfile prints a warning);
pass `--build-arg ACP_GOVERNANCE=required` for production images so a missing token fails the
build instead. CI installs the SDK and builds the governed image only when the repository secret
`GH_READ_TOKEN` is set. For a local venv: `pip install -r requirements-governance.txt` with the
same token configured in git.
