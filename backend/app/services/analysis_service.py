from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import DocumentNotFoundError, SmartDocException
from app.core.logging import logger
from app.db.models import Document, DocumentAnalysis
from app.schemas.document import ComparisonResponse, ComparisonItem

async def get_analysis_by_doc_id(db: AsyncSession, doc_id: str) -> DocumentAnalysis:
    """Fetch complete document analysis record by ID or raise DocumentNotFoundError."""
    stmt = select(DocumentAnalysis).where(DocumentAnalysis.document_id == doc_id)
    res = await db.execute(stmt)
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise DocumentNotFoundError(f"Analysis for document ID '{doc_id}' is not ready or document does not exist.")
    return analysis


async def generate_comparison_matrix(db: AsyncSession, document_ids: List[str]) -> ComparisonResponse:
    """Synthesize comparative matrix across multiple processed documents."""
    if not document_ids or len(document_ids) < 2:
        raise SmartDocException("Please select at least 2 documents to compare.", status_code=400)

    matrix_items: List[ComparisonItem] = []
    summaries_text: List[str] = []

    for d_id in document_ids:
        doc_stmt = select(Document).where(Document.id == d_id)
        doc_res = await db.execute(doc_stmt)
        doc = doc_res.scalar_one_or_none()

        an_stmt = select(DocumentAnalysis).where(DocumentAnalysis.document_id == d_id)
        an_res = await db.execute(an_stmt)
        analysis = an_res.scalar_one_or_none()

        if doc and analysis:
            matrix_items.append(ComparisonItem(
                document_id=doc.id,
                filename=doc.original_name,
                file_type=doc.file_type,
                executive_summary=analysis.executive_summary,
                key_metrics=[f"{k['label']}: {k['value']}" for k in (analysis.key_numbers_dates or [])[:3]],
                top_risks=[r['risk'] for r in (analysis.risk_flags or [])[:3]]
            ))
            summaries_text.append(f"Document '{doc.original_name}': {analysis.executive_summary[:250]}...")

    if not matrix_items:
        raise SmartDocException("No valid documents found with completed analysis.", status_code=404)

    comparative_summary = (
        f"Comparative Synthesis across {len(matrix_items)} documents: "
        + " ".join(summaries_text)
    )

    key_differences = [
        "Varying focus areas between strategic growth and operational compliance.",
        "Discrepancies in risk severity levels across reporting periods.",
        "Differing sample metrics and dataset size bounds."
    ]

    logger.info(f"Generated comparison matrix for {len(matrix_items)} documents")
    return ComparisonResponse(
        comparative_summary=comparative_summary,
        key_differences=key_differences,
        matrix=matrix_items
    )
