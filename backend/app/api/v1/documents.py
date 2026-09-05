from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.task_runner import process_document_background
from app.services import document_service

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    """
    Upload a document of any supported format or paste a web URL.
    Saves file to storage and triggers async background processing pipeline.
    """
    user = await document_service.get_or_create_dev_user(db)
    document = await document_service.create_document_record(db, file, url, user.id)
    background_tasks.add_task(process_document_background, document.id)
    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)) -> List[DocumentResponse]:
    """List all uploaded documents."""
    docs = await document_service.list_all_documents(db)
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)) -> DocumentResponse:
    """Fetch single document details."""
    doc = await document_service.get_document_by_id(db, doc_id)
    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str, db: AsyncSession = Depends(get_db)) -> DocumentStatusResponse:
    """Real-time status polling endpoint for tracking job progress."""
    doc = await document_service.get_document_by_id(db, doc_id)
    return DocumentStatusResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete document, uploaded file, and analysis records."""
    await document_service.delete_document_by_id(db, doc_id)
