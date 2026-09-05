from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.document import DocumentAnalysisResponse, ComparisonRequest, ComparisonResponse
from app.services import analysis_service

router = APIRouter()

@router.get("/{doc_id}", response_model=DocumentAnalysisResponse)
async def get_document_analysis(doc_id: str, db: AsyncSession = Depends(get_db)) -> DocumentAnalysisResponse:
    """Fetch complete analysis results for a document."""
    analysis = await analysis_service.get_analysis_by_doc_id(db, doc_id)
    return DocumentAnalysisResponse.model_validate(analysis)

@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(payload: ComparisonRequest, db: AsyncSession = Depends(get_db)) -> ComparisonResponse:
    """Cross-document comparison matrix generator."""
    return await analysis_service.generate_comparison_matrix(db, payload.document_ids)
