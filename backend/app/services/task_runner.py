from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Document, DocumentChunk, DocumentAnalysis
from app.extractors.router import extract_document_content
from app.services.chunker import chunk_document_pages
from app.services.map_reduce import process_map_reduce_analysis
from app.core.logging import logger

async def process_document_background(doc_id: str) -> None:
    """
    Background job runner for full document processing pipeline:
    Upload -> Format Detection & Extraction -> Chunking -> Map-Reduce Summarization -> Done
    """
    logger.info(f"Starting background processing for document: {doc_id}")
    async with AsyncSessionLocal() as db:
        stmt = select(Document).where(Document.id == doc_id)
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if not doc:
            logger.error(f"Background task aborted: Document ID '{doc_id}' not found in database.")
            return
            
        try:
            # Stage 1: Extraction & File Routing (15%)
            doc.status = "EXTRACTING"
            doc.progress_percent = 15
            doc.current_stage = f"Detecting format and extracting text for '{doc.original_name}'..."
            await db.commit()
            
            logger.info(f"Extracting content for doc_id={doc_id}, file_path={doc.file_path}")
            extracted = extract_document_content(doc.file_path, doc.original_name)
            
            doc.file_type = extracted["file_type"]
            doc.page_count = extracted["page_count"]
            
            # Stage 2: Chunking & Storage (35%)
            doc.status = "CHUNKING"
            doc.progress_percent = 35
            doc.current_stage = f"Generating page-aware chunks across {doc.page_count} page(s)..."
            await db.commit()
            
            logger.info(f"Chunking pages for doc_id={doc_id}, total_pages={doc.page_count}")
            chunks_data = chunk_document_pages(doc.id, extracted["pages"])
            
            # Save chunks to DB
            for c_info in chunks_data:
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c_info["chunk_index"],
                    page_number=c_info["page_number"],
                    content=c_info["content"],
                    token_count=c_info["token_count"]
                )
                db.add(chunk_record)
            await db.commit()
            logger.info(f"Persisted {len(chunks_data)} chunks to DB for doc_id={doc_id}")
            
            # Stage 3: Map-Reduce Summarization / Tabular Analysis (60%)
            doc.status = "SUMMARIZING"
            doc.progress_percent = 60
            if extracted["is_tabular"]:
                doc.current_stage = "Executing pandas statistical profiling & trend analysis..."
            else:
                doc.current_stage = "Running LLM Provider summarization & entity extraction..."
            await db.commit()
            
            analysis_data = await process_map_reduce_analysis(
                doc_id=doc.id,
                filename=doc.original_name,
                chunks=chunks_data,
                is_tabular=extracted["is_tabular"],
                tabular_stats=extracted["tabular_stats"]
            )
            
            # Save or Update Analysis Record
            existing_an_stmt = select(DocumentAnalysis).where(DocumentAnalysis.document_id == doc.id)
            existing_an_res = await db.execute(existing_an_stmt)
            analysis_record = existing_an_res.scalar_one_or_none()

            if not analysis_record:
                analysis_record = DocumentAnalysis(document_id=doc.id)
                db.add(analysis_record)

            analysis_record.executive_summary = analysis_data.get("executive_summary", "Summary completed.")
            analysis_record.detailed_summary = analysis_data.get("detailed_summary", "Detailed breakdown completed.")
            analysis_record.entities = analysis_data.get("entities", [])
            analysis_record.topics = analysis_data.get("topics", [])
            analysis_record.sentiment_tone = analysis_data.get("sentiment_tone", {})
            analysis_record.key_numbers_dates = analysis_data.get("key_numbers_dates", [])
            analysis_record.risk_flags = analysis_data.get("risk_flags", [])
            analysis_record.action_items = analysis_data.get("action_items", [])
            analysis_record.tabular_metrics = analysis_data.get("tabular_metrics", {})
            analysis_record.is_fallback = analysis_data.get("is_fallback", False)
            analysis_record.fallback_notice = analysis_data.get("fallback_notice")
            
            # Stage 4: Done (100%)
            doc.status = "COMPLETE"
            doc.progress_percent = 100
            doc.current_stage = "Analysis complete." + (" (Fallback Mode)" if analysis_data.get("is_fallback") else "")
            await db.commit()
            logger.info(f"Successfully finished document processing pipeline for doc_id={doc_id}")
            
        except Exception as e:
            logger.error(f"Processing failed for doc_id={doc_id}: {e}", exc_info=True)
            await db.rollback()
            stmt = select(Document).where(Document.id == doc_id)
            res = await db.execute(stmt)
            fail_doc = res.scalar_one_or_none()
            if fail_doc:
                fail_doc.status = "FAILED"
                fail_doc.progress_percent = 0
                fail_doc.current_stage = "Processing failed."
                fail_doc.error_message = str(e)
                await db.commit()
