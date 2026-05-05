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


def test_all_backend_nodes_are_callable():
    nodes = [
        bureau_pull_node, income_verification_node, risk_assessment_node,
        fraud_detection_node, score_aggregation_node, compliance_node,
        pricing_node, decision_node, offer_generation_node, human_review_node,
    ]
    for node in nodes:
        assert callable(node), f"{node.__name__} is not callable"
