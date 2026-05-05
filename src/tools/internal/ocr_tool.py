from __future__ import annotations

import structlog
from src.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Document type to Azure model mapping
_MODEL_MAP = {
    "pan_card": "prebuilt-idDocument",
    "aadhaar": "prebuilt-idDocument",
    "voter_id": "prebuilt-idDocument",
    "passport": "prebuilt-idDocument",
    "bank_statement": "prebuilt-document",
    "payslip": "prebuilt-document",
    "form_16": "prebuilt-document",
    "itr": "prebuilt-document",
    "gst_certificate": "prebuilt-document",
    "address_proof": "prebuilt-document",
    "selfie": None,  # Photo — no OCR, used for face matching
}


async def extract_document_data(document_url: str, document_type: str) -> dict:
    """Extract structured data from a document using Azure Document Intelligence.

    Supports both local file paths (file:// or /path) and remote URLs.
    Uses SDK v1.0.x API (body= parameter, bytes for local files).
    """
    if not settings.azure_doc_intelligence_endpoint:
        logger.info("no_doc_intelligence_endpoint, using_mock", document_type=document_type)
        return _get_mock_extraction(document_type)

    model_id = _MODEL_MAP.get(document_type, "prebuilt-document")

    # Photos don't need OCR
    if model_id is None:
        logger.info("skipping_ocr_for_photo", document_type=document_type)
        return {
            "key_value_pairs": {},
            "tables": [],
            "text": "",
            "confidence": 1.0,
            "document_type": document_type,
            "model_used": "none (photo)",
            "photo_url": document_url,
        }

    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    client = DocumentIntelligenceClient(
        endpoint=settings.azure_doc_intelligence_endpoint,
        credential=AzureKeyCredential(settings.azure_doc_intelligence_key),
    )

    try:
        # Determine if local file or remote URL
        is_local = document_url.startswith("file://") or document_url.startswith("/")
        if is_local:
            file_path = document_url.replace("file://", "")
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            # SDK v1.0.x: send bytes with content_type
            poller = client.begin_analyze_document(
                model_id,
                body=file_bytes,
                content_type="application/octet-stream",
            )
        else:
            # Remote URL — SDK v1.0.x
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            poller = client.begin_analyze_document(
                model_id,
                body=AnalyzeDocumentRequest(url_source=document_url),
            )

        result = poller.result()

        extracted = {
            "key_value_pairs": {},
            "tables": [],
            "text": "",
            "confidence": 0.0,
            "document_type": document_type,
            "model_used": model_id,
        }

        # Extract key-value pairs
        if result.key_value_pairs:
            for kv in result.key_value_pairs:
                if kv.key and kv.value:
                    key_text = kv.key.content if hasattr(kv.key, "content") else str(kv.key)
                    val_text = kv.value.content if hasattr(kv.value, "content") else str(kv.value)
                    extracted["key_value_pairs"][key_text] = val_text

        # Extract tables
        if result.tables:
            for table in result.tables:
                table_data = []
                for cell in table.cells:
                    table_data.append({
                        "row": cell.row_index,
                        "col": cell.column_index,
                        "content": cell.content,
                    })
                extracted["tables"].append(table_data)

        # Extract full text
        if result.content:
            extracted["text"] = result.content

        # Extract ID document fields (PAN, Aadhaar, passport)
        if result.documents:
            for doc in result.documents:
                if doc.fields:
                    for field_name, field_value in doc.fields.items():
                        if field_value and hasattr(field_value, "content") and field_value.content:
                            extracted["key_value_pairs"][field_name] = field_value.content
                        elif field_value and hasattr(field_value, "value_string") and field_value.value_string:
                            extracted["key_value_pairs"][field_name] = field_value.value_string
                if doc.confidence:
                    extracted["confidence"] = doc.confidence

        logger.info(
            "doc_intelligence_extraction_complete",
            document_type=document_type,
            model=model_id,
            keys_found=len(extracted["key_value_pairs"]),
            confidence=extracted["confidence"],
        )
        return extracted

    except Exception as e:
        logger.error("doc_intelligence_extraction_failed", error=str(e), document_type=document_type)
        # Fall back to mock in dev if real extraction fails
        if settings.is_development:
            logger.info("falling_back_to_mock", document_type=document_type)
            return _get_mock_extraction(document_type)
        return {
            "key_value_pairs": {},
            "tables": [],
            "text": "",
            "confidence": 0.0,
            "error": str(e),
            "document_type": document_type,
        }


def _get_mock_extraction(document_type: str) -> dict:
    """Return mock OCR data for development when no Azure endpoint is configured."""
    mocks = {
        "pan_card": {
            "key_value_pairs": {
                "Name": "Raj Kumar",
                "PAN": "ABCDE1234F",
                "Date of Birth": "15/03/1990",
                "Father's Name": "Suresh Kumar",
            },
            "tables": [],
            "text": "INCOME TAX DEPARTMENT\nPERMANENT ACCOUNT NUMBER CARD\nABCDE1234F\nRAJ KUMAR",
            "confidence": 0.95,
            "document_type": "pan_card",
        },
        "aadhaar": {
            "key_value_pairs": {
                "Name": "Raj Kumar",
                "Aadhaar Number": "XXXX XXXX 1234",
                "Date of Birth": "15/03/1990",
                "Address": "123 MG Road, Mumbai 400001",
                "Gender": "Male",
            },
            "tables": [],
            "text": "Government of India\nAadhaar\nRaj Kumar\nDOB: 15/03/1990",
            "confidence": 0.92,
            "document_type": "aadhaar",
        },
        "bank_statement": {
            "key_value_pairs": {
                "Account Holder": "Raj Kumar",
                "Account Number": "XXXX1234",
                "Bank": "HDFC Bank",
                "Statement Period": "Jan 2026 - Mar 2026",
                "Closing Balance": "125000.00",
            },
            "tables": [
                [
                    {"row": 0, "col": 0, "content": "Date"},
                    {"row": 0, "col": 1, "content": "Description"},
                    {"row": 0, "col": 2, "content": "Amount"},
                    {"row": 1, "col": 0, "content": "01/01/2026"},
                    {"row": 1, "col": 1, "content": "Salary Credit - TCS LTD"},
                    {"row": 1, "col": 2, "content": "75000.00"},
                ]
            ],
            "text": "HDFC Bank Statement for Raj Kumar",
            "confidence": 0.88,
            "document_type": "bank_statement",
        },
        "payslip": {
            "key_value_pairs": {
                "Employee Name": "Raj Kumar",
                "Employee ID": "TCS-78456",
                "Gross Salary": "85000",
                "Net Salary": "72000",
                "Employer": "TCS Ltd",
                "Month": "March 2026",
            },
            "tables": [],
            "text": "Payslip for month of March 2026",
            "confidence": 0.90,
            "document_type": "payslip",
        },
        "selfie": {
            "key_value_pairs": {},
            "tables": [],
            "text": "",
            "confidence": 1.0,
            "document_type": "selfie",
            "model_used": "none (photo)",
            "face_detected": True,
            "liveness_score": 0.95,
        },
    }
    result = mocks.get(document_type, {
        "key_value_pairs": {},
        "tables": [],
        "text": f"Mock extraction for {document_type}",
        "confidence": 0.85,
        "document_type": document_type,
    })
    logger.info("mock_extraction_used", document_type=document_type)
    return result
