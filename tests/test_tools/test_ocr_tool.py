import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def _force_mock_mode():
    """Force OCR tool into mock mode by clearing the cached settings and endpoint."""
    from src.config import get_settings, Settings
    # Clear lru_cache so we get fresh settings
    get_settings.cache_clear()
    # Patch the module-level settings used in ocr_tool
    import src.tools.internal.ocr_tool as ocr_mod
    mock_settings = MagicMock(spec=Settings)
    mock_settings.is_development = True
    mock_settings.azure_doc_intelligence_endpoint = ""
    mock_settings.azure_doc_intelligence_key = ""
    with patch.object(ocr_mod, "settings", mock_settings):
        yield
    get_settings.cache_clear()


from src.tools.internal.ocr_tool import extract_document_data, _get_mock_extraction


@pytest.mark.asyncio
async def test_mock_extraction_pan():
    result = await extract_document_data("file://test.pdf", "pan_card")
    assert result["document_type"] == "pan_card"
    assert "Name" in result["key_value_pairs"]
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_mock_extraction_aadhaar():
    result = await extract_document_data("file://test.pdf", "aadhaar")
    assert result["document_type"] == "aadhaar"
    assert "Aadhaar Number" in result["key_value_pairs"]


@pytest.mark.asyncio
async def test_mock_extraction_bank_statement():
    result = await extract_document_data("file://test.pdf", "bank_statement")
    assert result["document_type"] == "bank_statement"
    assert len(result["tables"]) > 0


@pytest.mark.asyncio
async def test_mock_extraction_unknown_type():
    result = await extract_document_data("file://test.pdf", "unknown_doc")
    assert result["document_type"] == "unknown_doc"
    assert result["confidence"] > 0


def test_mock_extraction_helper():
    result = _get_mock_extraction("payslip")
    assert result["key_value_pairs"]["Employer"] == "TCS Ltd"
