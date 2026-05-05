"""LangGraph StateGraph definition for loan underwriting. 13 nodes across 5 phases."""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.graph.state import LoanApplicationState
from src.graph.nodes.intake import intake_collect_info, intake_loan_details
from src.graph.nodes.doc_collection import doc_collection_node
from src.graph.nodes.doc_verification import doc_verification_node
from src.graph.nodes.bureau_pull import bureau_pull_node
from src.graph.nodes.income_verification import income_verification_node
from src.graph.nodes.risk_assessment import risk_assessment_node
from src.graph.nodes.fraud_detection import fraud_detection_node
from src.graph.nodes.score_aggregation import score_aggregation_node
from src.graph.nodes.compliance import compliance_node
from src.graph.nodes.pricing import pricing_node
from src.graph.nodes.decision import decision_node
from src.graph.nodes.offer_generation import offer_generation_node
from src.graph.nodes.human_review import human_review_node


def _route_after_decision(state: LoanApplicationState) -> str:
    decision = state.get("decision", "")
    if decision == "escalated" or state.get("needs_human_review"):
        return "human_review"
    if decision == "denied":
        return END
    return "offer_generation"


_compiled_graph_cache: dict[int, object] = {}


def build_graph(checkpointer=None):
    """Build and compile the loan underwriting StateGraph.

    Intake is split into two nodes (intake_collect_info + intake_loan_details),
    each with its own interrupt() call. This avoids Command(goto=...) loops
    which break interrupt() in LangGraph 1.x.
    """
    cache_key = id(checkpointer)
    if cache_key in _compiled_graph_cache:
        return _compiled_graph_cache[cache_key]

    builder = StateGraph(LoanApplicationState)

    builder.add_node("intake_collect_info", intake_collect_info)
    builder.add_node("intake_loan_details", intake_loan_details)
    builder.add_node("doc_collection", doc_collection_node)
    builder.add_node("doc_verification", doc_verification_node)
    builder.add_node("bureau_pull", bureau_pull_node)
    builder.add_node("income_verification", income_verification_node)
    builder.add_node("risk_assessment", risk_assessment_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("score_aggregation", score_aggregation_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("pricing", pricing_node)
    builder.add_node("decision", decision_node)
    builder.add_node("offer_generation", offer_generation_node)
    builder.add_node("human_review", human_review_node)

    # Phase 1: Intake — two separate nodes, each with its own interrupt()
    builder.add_edge(START, "intake_collect_info")
    builder.add_edge("intake_collect_info", "intake_loan_details")
    builder.add_edge("intake_loan_details", "doc_collection")
    # Phase 2: Extraction
    builder.add_edge("doc_collection", "doc_verification")
    builder.add_edge("doc_verification", "bureau_pull")
    builder.add_edge("doc_verification", "income_verification")
    # Phase 3: Risk (after bureau + income)
    builder.add_edge("bureau_pull", "risk_assessment")
    builder.add_edge("income_verification", "risk_assessment")
    builder.add_edge("risk_assessment", "fraud_detection")
    builder.add_edge("fraud_detection", "score_aggregation")
    # Phase 4: Decision
    builder.add_edge("score_aggregation", "compliance")
    builder.add_edge("score_aggregation", "pricing")
    builder.add_edge("compliance", "decision")
    builder.add_edge("pricing", "decision")
    # Conditional routing
    builder.add_conditional_edges("decision", _route_after_decision)
    # Terminal
    builder.add_edge("offer_generation", END)
    builder.add_edge("human_review", END)

    # Intake and doc_collection handle their own interrupts via interrupt()
    compiled = builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["offer_generation", "human_review"],
    )
    _compiled_graph_cache[cache_key] = compiled
    return compiled
