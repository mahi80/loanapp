from src.graph.nodes.doc_collection import doc_collection_node
from src.graph.nodes.doc_verification import doc_verification_node
from src.graph.nodes.intake import intake_collect_info, intake_loan_details


def test_intake_collect_info_is_callable():
    assert callable(intake_collect_info)


def test_intake_loan_details_is_callable():
    assert callable(intake_loan_details)


def test_doc_collection_node_is_callable():
    assert callable(doc_collection_node)


def test_doc_verification_node_is_callable():
    assert callable(doc_verification_node)
