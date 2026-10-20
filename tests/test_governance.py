"""ACP governance wiring (src/graph/governance.py) — env-gated, never breaks the graph."""

from __future__ import annotations

import sys
import types

import pytest

from src.graph import governance


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    for var in (
        "ACP_DASHBOARD_URL",
        "ACP_API_KEY",
        "ACP_AGENT_CODE",
        "ACP_AGENT_NAME",
        "ACP_BU",
        "ACP_BUDGET",
        "ACP_TIER",
        "ACP_GOVERN",
        "ACP_PROCESS_NAME",
        "ACP_PROCESS_TYPE",
    ):
        monkeypatch.delenv(var, raising=False)
    governance.governed_state = None
    yield
    governance.governed_state = None


def _fake_acp(monkeypatch, calls: list, *, raise_exc: Exception | None = None):
    mod = types.ModuleType("acp")

    def govern(agent, **kw):
        calls.append((agent, kw))
        if raise_exc:
            raise raise_exc
        return ("governed", agent)

    mod.govern = govern
    monkeypatch.setitem(sys.modules, "acp", mod)


def test_disabled_without_dashboard_url(monkeypatch):
    calls: list = []
    _fake_acp(monkeypatch, calls)
    graph = object()
    assert governance.govern_graph(graph) is graph
    assert calls == [] and governance.governed_state is False


def test_governs_with_defaults_when_dashboard_url_set(monkeypatch):
    calls: list = []
    _fake_acp(monkeypatch, calls)
    monkeypatch.setenv("ACP_DASHBOARD_URL", "https://dashboard.acpgovernance.com")
    graph = object()
    out = governance.govern_graph(graph)
    assert out == ("governed", graph) and governance.governed_state is True
    ((agent, kw),) = calls
    assert agent is graph
    assert kw["agent_code"] == "LEN-LOA-01"
    assert kw["name"] == "lending-loan-processing-disbursement"
    assert kw["bu"] == "Lending" and kw["budget"] == 5.0 and kw["tier"] == "TIER_2"
    assert (
        kw["process_name"] == "loan-underwriting"
        and kw["process_type"] == "customer-facing"
    )
    assert kw["framework"] == "langgraph"


def test_env_overrides(monkeypatch):
    calls: list = []
    _fake_acp(monkeypatch, calls)
    monkeypatch.setenv("ACP_DASHBOARD_URL", "https://dash.test")
    monkeypatch.setenv("ACP_AGENT_CODE", "len-loa-02")
    monkeypatch.setenv("ACP_BU", "Retail")
    monkeypatch.setenv("ACP_BUDGET", "2.5")
    monkeypatch.setenv("ACP_TIER", "TIER_1")
    governance.govern_graph(object())
    kw = calls[0][1]
    assert kw["agent_code"] == "len-loa-02" and kw["bu"] == "Retail"
    assert kw["budget"] == 2.5 and kw["tier"] == "TIER_1"


def test_acp_govern_zero_forces_off(monkeypatch):
    calls: list = []
    _fake_acp(monkeypatch, calls)
    monkeypatch.setenv("ACP_DASHBOARD_URL", "https://dash.test")
    monkeypatch.setenv("ACP_GOVERN", "0")
    graph = object()
    assert governance.govern_graph(graph) is graph and calls == []


def test_missing_sdk_logs_and_returns_ungoverned(monkeypatch, caplog):
    monkeypatch.setitem(sys.modules, "acp", None)  # import acp -> ImportError
    monkeypatch.setenv("ACP_DASHBOARD_URL", "https://dash.test")
    graph = object()
    with caplog.at_level("ERROR"):
        assert governance.govern_graph(graph) is graph
    assert governance.governed_state is False
    assert "UNGOVERNED" in caplog.text


def test_govern_failure_never_breaks_the_graph(monkeypatch, caplog):
    calls: list = []
    _fake_acp(monkeypatch, calls, raise_exc=RuntimeError("license server down"))
    monkeypatch.setenv("ACP_DASHBOARD_URL", "https://dash.test")
    graph = object()
    with caplog.at_level("ERROR"):
        assert governance.govern_graph(graph) is graph
    assert governance.governed_state is False
    assert "license server down" in caplog.text
