from __future__ import annotations

import uuid
from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Document, DocumentType, OcrStatus, User
from src.auth.middleware import get_current_user
from src.api.models.schemas import DocumentUploadResponse, DocumentResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Supported MIME types for document upload (Azure Doc Intelligence supported formats)
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/heif",
    "image/heic",
    "image/webp",
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".heif", ".heic", ".webp"}


async def _upload_to_blob(content: bytes, blob_name: str) -> str:
    """Upload file to Azure Blob Storage and return the blob URL."""
    from src.config import get_settings
    settings = get_settings()

    if not settings.azure_blob_connection_string or settings.environment == "development":
        # Dev fallback: save locally
        import os
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, blob_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(content)
        return f"file://{os.path.abspath(local_path)}"

    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

    blob_service = BlobServiceClient.from_connection_string(settings.azure_blob_connection_string)
    container_client = blob_service.get_container_client(settings.azure_blob_container)

    # Create container if it doesn't exist
    try:
        container_client.create_container()
    except Exception:
        pass  # Container already exists

    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(content, overwrite=True)

    # Generate SAS URL for Document Intelligence to access
    sas_token = generate_blob_sas(
        account_name=blob_service.account_name,
        container_name=settings.azure_blob_container,
        blob_name=blob_name,
        account_key=blob_service.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(UTC) + timedelta(hours=1),
    )

    return f"{blob_client.url}?{sas_token}"


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    application_id: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document (PDF or image), store in Azure Blob, trigger OCR extraction.

    Supported formats: PDF, JPEG, PNG, TIFF, BMP, HEIF, WebP.
    """
    from pathlib import PurePosixPath

    # Validate file type
    ext = PurePosixPath(file.filename or "").suffix.lower()
    content_type = file.content_type or ""
    if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or content_type}'. "
                   f"Accepted: PDF, JPEG, PNG, TIFF, BMP, HEIF, WebP.",
        )

    # Resolve application_id (may be "pending" or empty during chat-based upload)
    app_id: uuid.UUID | None = None
    if application_id and application_id != "pending":
        try:
            app_id = uuid.UUID(application_id)
        except ValueError:
            pass  # Not a valid UUID — treat as unlinked upload

    # Sanitize filename to prevent path traversal
    safe_filename = PurePosixPath(file.filename or "document").name
    if not safe_filename or safe_filename.startswith("."):
        safe_filename = f"{uuid.uuid4().hex[:12]}"
    unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
    folder = str(app_id) if app_id else f"user_{user.id}"
    blob_name = f"documents/{folder}/{unique_filename}"

    content = await file.read()

    # Validate file size (10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 10MB")

    # Upload to Azure Blob Storage (or local in dev)
    blob_url = await _upload_to_blob(content, blob_name)

    # Create document record (application_id is nullable for chat-uploaded docs)
    doc = Document(
        application_id=app_id,
        type=document_type,
        file_path=blob_url,
        ocr_status=OcrStatus.PROCESSING,
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    # Trigger OCR extraction
    try:
        from src.tools.internal.ocr_tool import extract_document_data
        extracted = await extract_document_data(blob_url, document_type.value)
        doc.extracted_data = extracted
        doc.ocr_status = OcrStatus.COMPLETED
        doc.classification_confidence = extracted.get("confidence", 0.0)
    except Exception as e:
        doc.ocr_status = OcrStatus.FAILED
        doc.extracted_data = {"error": str(e)}

    return DocumentUploadResponse(
        document_id=doc.id,
        status="uploaded",
        ocr_status=doc.ocr_status,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get extracted data from a processed document (auth required)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Ensure the requesting user owns the document or its application
    if doc.uploaded_by and doc.uploaded_by != user.id and user.role.value != "officer":
        raise HTTPException(status_code=403, detail="Access denied")

    return DocumentResponse(
        document_id=doc.id,
        type=doc.type,
        ocr_status=doc.ocr_status,
        extracted_data=doc.extracted_data,
    )


@router.get("/{document_id}/extraction")
async def get_extraction(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get OCR extraction results for a document (auth required)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.uploaded_by and doc.uploaded_by != user.id and user.role.value != "officer":
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "document_id": str(doc.id),
        "type": doc.type.value,
        "ocr_status": doc.ocr_status.value,
        "extracted_data": doc.extracted_data,
        "confidence": doc.classification_confidence,
    }
