"""ACP governance for the loan underwriting graph (LEN-LOA-01).

Wraps the compiled LangGraph with ``acp.govern()`` so every node runs
under the ACP controls (loop guard, cost gate, autonomy tier, Q37
infrastructure guard, ...), the agent registers with the dashboard,
heartbeats every 10 s, and honours the dashboard's pause-gate.

Opt-in by environment so local development and the test suite run exactly
as before when ACP is not configured:

    ACP_DASHBOARD_URL   e.g. https://dashboard.acpgovernance.com  (required to enable)
    ACP_API_KEY         dashboard agent API key
    ACP_AGENT_CODE      default LEN-LOA-01   (must match the onboarded agent_code)
    ACP_AGENT_NAME      default lending-loan-processing-disbursement
    ACP_BU              default Lending
    ACP_BUDGET          default 5.0 (USD per task)
    ACP_TIER            default TIER_2
    ACP_GOVERN          "0" disables the wrap even when ACP_DASHBOARD_URL is set

The wrap never breaks the app: if the SDK is missing or ``govern()`` fails
the graph is returned un-governed and the problem is logged at ERROR, so
a misconfigured deploy still serves loans while the operator fixes it —
the dashboard will show the agent silent, which the rogue scanner flags.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

AGENT_CODE_DEFAULT = "LEN-LOA-01"
AGENT_NAME_DEFAULT = "lending-loan-processing-disbursement"
BU_DEFAULT = "Lending"
PROCESS_NAME = "loan-underwriting"
PROCESS_TYPE = "customer-facing"

#: Set after the first build: None = not attempted, True = governed, False = failed/disabled.
governed_state: bool | None = None


def governance_enabled() -> bool:
    if os.environ.get("ACP_GOVERN", "1").strip().lower() in {"0", "false", "no", "off"}:
        return False
    return bool(os.environ.get("ACP_DASHBOARD_URL", "").strip())


def governance_settings() -> dict[str, Any]:
    return {
        "name": os.environ.get("ACP_AGENT_NAME", AGENT_NAME_DEFAULT),
        "agent_code": os.environ.get("ACP_AGENT_CODE", AGENT_CODE_DEFAULT),
        "bu": os.environ.get("ACP_BU", BU_DEFAULT),
        "process_name": os.environ.get("ACP_PROCESS_NAME", PROCESS_NAME),
        "process_type": os.environ.get("ACP_PROCESS_TYPE", PROCESS_TYPE),
        "budget": float(os.environ.get("ACP_BUDGET", "5.0")),
        "tier": os.environ.get("ACP_TIER", "TIER_2"),
        "framework": "langgraph",
    }


def govern_graph(compiled: Any) -> Any:
    """Return the governed graph, or the same graph when ACP is not configured."""
    global governed_state
    if not governance_enabled():
        governed_state = False
        return compiled
    try:
        from acp import govern  # acp-sdk, see requirements.txt
    except ImportError as e:
        governed_state = False
        logger.error("ACP_DASHBOARD_URL is set but acp-sdk is not installed (%s); graph runs UNGOVERNED", e)
        return compiled
    settings = governance_settings()
    try:
        governed = govern(compiled, **settings)
    except Exception as e:  # noqa: BLE001 — never take the loan app down over governance wiring
        governed_state = False
        logger.error("acp.govern() failed for %s (%s); graph runs UNGOVERNED", settings["agent_code"], e)
        return compiled
    governed_state = True
    logger.info(
        "ACP governance active: %s (%s, bu=%s, tier=%s, budget=$%.2f) -> %s",
        settings["agent_code"], settings["name"], settings["bu"], settings["tier"],
        settings["budget"], os.environ.get("ACP_DASHBOARD_URL", ""),
    )
    return governed
