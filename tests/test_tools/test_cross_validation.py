from src.graph.tools import cross_validate_documents


def test_matching_documents():
    docs = {
        "pan_card": {"key_value_pairs": {"Name": "Raj Kumar", "Date of Birth": "15/03/1990"}},
        "aadhaar": {"key_value_pairs": {"Name": "Raj Kumar", "DOB": "15/03/1990"}},
    }
    result = cross_validate_documents.invoke({"documents": docs})
    assert result["valid"] is True
    assert len(result["issues"]) == 0


def test_name_mismatch():
    docs = {
        "pan_card": {"key_value_pairs": {"Name": "Raj Kumar"}},
        "bank_statement": {"key_value_pairs": {"Account Holder": "Rajesh Kumar"}},
    }
    result = cross_validate_documents.invoke({"documents": docs})
    assert result["valid"] is False
    assert any(i["type"] == "name_mismatch" for i in result["issues"])
