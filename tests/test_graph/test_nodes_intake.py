from src.graph.nodes.intake import intake_node
from src.graph.nodes.doc_collection import doc_collection_node
from src.graph.nodes.doc_verification import doc_verification_node


def test_intake_node_is_callable():
    assert callable(intake_node)


def test_doc_collection_node_is_callable():
    assert callable(doc_collection_node)


def test_doc_verification_node_is_callable():
    assert callable(doc_verification_node)
