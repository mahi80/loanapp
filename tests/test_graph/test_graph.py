from src.graph.graph import build_graph


def test_build_graph_returns_compiled_graph():
    graph = build_graph()
    assert graph is not None
    assert hasattr(graph, "ainvoke")
    assert hasattr(graph, "astream")


def test_graph_has_all_nodes():
    graph = build_graph()
    node_names = set(graph.nodes.keys())
    expected = {
        "intake", "doc_collection", "doc_verification",
        "bureau_pull", "income_verification",
        "risk_assessment", "fraud_detection", "score_aggregation",
        "compliance", "pricing", "decision",
        "offer_generation", "human_review",
    }
    for name in expected:
        assert name in node_names, f"Missing node: {name}"
