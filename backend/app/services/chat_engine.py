from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DocumentChunk
from app.services.llm_provider import get_llm_provider

async def answer_document_query(
    db: AsyncSession,
    document_ids: List[str],
    user_query: str,
    chat_history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Grounded Chat Engine querying document chunks and yielding cited AI answers via configured LLMProvider.
    """
    stmt = select(DocumentChunk).where(DocumentChunk.document_id.in_(document_ids)).limit(20)
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    
    if not chunks:
        return {
            "answer": "No extracted document context found for the selected document(s). Please verify processing status.",
            "citations": []
        }
        
    context_chunks = [
        {
            "doc_id": c.document_id,
            "chunk_id": f"CHUNK-{c.document_id[:8]}-P{c.page_number or 1}-C{c.chunk_index}",
            "page_number": c.page_number,
            "content": c.content
        } for c in chunks
    ]
    
    provider = get_llm_provider()
    return await provider.chat(
        user_query=user_query,
        context_chunks=context_chunks,
        chat_history=chat_history
    )
