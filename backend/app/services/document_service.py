import os
import uuid
import shutil
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import DocumentNotFoundError, UnsupportedFileTypeError, SmartDocException
from app.db.models import Document, User
from fastapi import UploadFile

async def get_or_create_dev_user(db: AsyncSession) -> User:
    """Fetch existing dev demo user or create one if absent."""
    stmt = select(User).where(User.email == "demo@smartdoc.ai")
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="demo@smartdoc.ai",
            hashed_password="demo_password_hash",
            full_name="Demo User"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Created default demo user [demo@smartdoc.ai]")
    return user


async def create_document_record(
    db: AsyncSession,
    file: Optional[UploadFile],
    url: Optional[str],
    user_id: str
) -> Document:
    """
    Validates upload source (file or URL), saves file payload to storage,
    and initializes PENDING Document database record.
    """
    if not file and not url:
        raise SmartDocException("Either a file upload or a valid web URL must be provided.", status_code=400)

    doc_id = str(uuid.uuid4())

    if url:
        original_name = url.split('/')[-1] or "webpage.html"
        filename = f"{doc_id}_{original_name}"
        file_path = url
        file_size = 1024
        file_type = "html"
        logger.info(f"Received URL upload task: doc_id={doc_id}, url={url}")
    else:
        assert file is not None and file.filename is not None
        original_name = file.filename
        file_ext = os.path.splitext(original_name)[1]
        filename = f"{doc_id}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)
        file_type = file_ext.replace('.', '') or "unknown"
        logger.info(f"Saved uploaded file to storage: doc_id={doc_id}, size={file_size} bytes, type={file_type}")

    document = Document(
        id=doc_id,
        user_id=user_id,
        filename=filename,
        original_name=original_name,
        file_type=file_type,
        file_size_bytes=file_size,
        file_path=file_path,
        status="PENDING",
        progress_percent=5,
        current_stage="File queued for processing"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def list_all_documents(db: AsyncSession) -> List[Document]:
    """Retrieve all uploaded documents ordered by creation date descending."""
    stmt = select(Document).order_by(Document.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_document_by_id(db: AsyncSession, doc_id: str) -> Document:
    """Fetch single document record by ID or raise DocumentNotFoundError."""
    stmt = select(Document).where(Document.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise DocumentNotFoundError(f"Document with ID '{doc_id}' not found.")
    return doc


async def delete_document_by_id(db: AsyncSession, doc_id: str) -> None:
    """Delete document DB record and remove raw storage file if present."""
    doc = await get_document_by_id(db, doc_id)
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
            logger.info(f"Removed file from disk: {doc.file_path}")
        except Exception as err:
            logger.warning(f"Could not remove file at {doc.file_path}: {err}")

    await db.delete(doc)
    await db.commit()
    logger.info(f"Deleted document record doc_id={doc_id}")
