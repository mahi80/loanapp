from __future__ import annotations

import json
import uuid as _uuid
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt
from sqlalchemy import select

from src.graph.state import LoanApplicationState
from src.db.session import async_session_factory
from src.db.models import ProductRule, LoanType, Document

# Human-readable labels for document types
_DOC_LABELS = {
    "pan_card": "PAN Card",
    "aadhaar": "Aadhaar Card",
    "selfie": "Applicant Photograph",
    "bank_statement": "Bank Statement (last 6 months)",
    "address_proof": "Address Proof",
    "payslip": "Latest Payslip",
    "form_16": "Form 16",
    "employment_letter": "Employment Letter",
    "salary_certificate": "Salary Certificate",
    "itr": "ITR (last 2 years)",
    "gst_certificate": "GST Certificate",
    "business_registration": "Business Registration",
    "pnl_statement": "P&L Statement",
    "balance_sheet": "Balance Sheet",
}


async def _get_doc_requirements_from_db(
    loan_type: str,
    employment_type: str,
) -> list[str] | None:
    """Query database for document requirements based on loan type."""
    try:
        async with async_session_factory() as session:
            stmt = select(ProductRule).where(
                ProductRule.product_type == LoanType(loan_type),
                ProductRule.rule_name == "document_requirements",
                ProductRule.active == True,
            )
            result = await session.execute(stmt)
            rule = result.scalar_one_or_none()

            if not rule:
                return None

            rule_config = rule.rule_config
            if not isinstance(rule_config, dict) or "groups" not in rule_config:
                return None

            required_docs = []
            groups = rule_config.get("groups", [])

            for group in groups:
                group_name = group.get("group")
                if group_name == "all" or group_name == employment_type:
                    docs = group.get("documents", [])
                    for doc in docs:
                        if doc.get("enabled") and doc.get("tier") in ["mandatory", "recommended"]:
                            required_docs.append(doc.get("key"))

            return required_docs if required_docs else None
    except Exception:
        return None


async def doc_collection_node(state: LoanApplicationState) -> dict:
    """Determine required documents and interrupt to show upload widgets.

    Uses interrupt() to pause and send upload widgets to the frontend.
    No LLM call needed — deterministic based on DB rules.
    """
    loan_type = state.get("loan_type", "personal")
    employment = state.get("employment_type", "salaried")
    name = state.get("applicant_name", "Customer")

    required = await _get_doc_requirements_from_db(loan_type, employment)

    if required is None:
        required = ["pan_card", "aadhaar", "selfie", "bank_statement"]
        if employment == "salaried":
            required.extend(["payslip", "form_16"])
        elif employment == "self_employed":
            required.extend(["itr", "gst_certificate"])

    uploaded = list(state.get("documents_uploaded", {}).keys())
    pending = [d for d in required if d not in uploaded]

    # Build tool list for the interrupt payload
    tools = []
    for doc in pending:
        label = _DOC_LABELS.get(doc, doc.replace("_", " ").title())
        tools.append({"name": "upload_document", "args": {"document_type": doc, "label": label}})

    text = (
        f"Great, {name}! Now let's collect your documents. "
        f"Please upload the {len(pending)} required documents below."
    )

    # Pause — frontend renders upload widgets via interrupt payload
    upload_data = interrupt({
        "__interrupt_type__": "multi_upload",
        "progress": {"step": 3, "total": 5, "label": "Document Upload"},
        "tools": tools,
        "text": text,
    })

    # Resumed — upload_data may be:
    #   (a) batched: {"tool": "documents_submitted", "documents": [{document_type, document_id, file_name}, ...]}
    #   (b) single (legacy): {"tool": "upload_document", "document_type": "...", "document_id": "..."}
    batch_docs: list[dict] = []
    if isinstance(upload_data, dict):
        tool_kind = upload_data.get("tool")
        if tool_kind == "documents_submitted":
            raw = upload_data.get("documents") or []
            if isinstance(raw, list):
                batch_docs = [d for d in raw if isinstance(d, dict) and d.get("document_id")]
        elif tool_kind == "upload_document" and upload_data.get("document_id"):
            batch_docs = [upload_data]

    # Hydrate state.documents_uploaded with DB-persisted extraction (OCR happens at upload time).
    uploaded_map = dict(state.get("documents_uploaded") or {})
    doc_ids: list[_uuid.UUID] = []
    for d in batch_docs:
        try:
            doc_ids.append(_uuid.UUID(str(d["document_id"])))
        except (ValueError, KeyError, TypeError):
            continue

    if doc_ids:
        async with async_session_factory() as session:
            result = await session.execute(select(Document).where(Document.id.in_(doc_ids)))
            for doc in result.scalars().all():
                key = doc.type.value.lower() if doc.type else "unknown"
                uploaded_map[key] = {
                    "document_id": str(doc.id),
                    "file_path": doc.file_path,
                    "extracted_data": doc.extracted_data,
                    "confidence": doc.classification_confidence,
                    "ocr_status": doc.ocr_status.value if doc.ocr_status else None,
                }

    return {
        "messages": [HumanMessage(content=json.dumps(upload_data))],
        "documents_required": required,
        "documents_pending": [d for d in required if d not in uploaded_map],
        "documents_uploaded": uploaded_map,
        "current_phase": "doc_verification",
    }
