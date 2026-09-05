import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import SmartDocException
from app.db.models import ChatSession, ChatMessage
from app.schemas.document import (
    ChatMessageRequest,
    ChatMessageResponse,
    CitationItem,
    WebCitationItem,
    WebSearchChatRequest
)
from app.services.chat_engine import answer_document_query
from app.services.web_search_service import execute_web_search_and_synthesize
from app.services import document_service

def is_not_found_in_document(answer: str) -> bool:
    """Detect if the LLM grounded response indicates the information is missing from the document."""
    if not answer:
        return True
    ans_lower = answer.lower()
    refusal_phrases = [
        "do not contain information",
        "does not contain information",
        "do not contain any information",
        "does not contain any information",
        "not mentioned",
        "not covered",
        "does not mention",
        "no information",
        "cannot be answered",
        "unable to find",
        "not found",
        "no extracted document context",
        "does not provide",
        "do not provide",
        "no evaluation",
        "cannot evaluate",
        "unable to evaluate",
        "no rating",
        "no ranking",
        "not provide a comprehensive",
        "does not assess",
        "no data on whether",
        "does not evaluate",
        "inquired about the quality"
    ]
    return any(phrase in ans_lower for phrase in refusal_phrases)


async def process_chat_message(db: AsyncSession, payload: ChatMessageRequest) -> ChatMessageResponse:
    """Handles grounded chat processing, session management, and response generation."""
    user = await document_service.get_or_create_dev_user(db)

    if not payload.document_ids:
        raise SmartDocException("Please specify at least one document ID for chat context.", status_code=400)

    session_id = payload.session_id
    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Document Q&A Session",
            document_ids=payload.document_ids
        )
        db.add(session)
        await db.commit()
        session_id = session.id

    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        sender="user",
        content=payload.message,
        citations=[]
    )
    db.add(user_msg)
    await db.commit()

    logger.info(f"Processing chat query for session '{session_id}' across {len(payload.document_ids)} docs")
    result = await answer_document_query(db, payload.document_ids, payload.message)
    answer_text = result.get("answer", "")

    citations = [
        CitationItem(
            doc_id=c["doc_id"],
            chunk_id=c["chunk_id"],
            page_number=c.get("page_number"),
            snippet=c["snippet"]
        ) for c in result.get("citations", [])
    ]

    offer_web_search = False
    web_prompt = None
    if settings.WEB_SEARCH_ENABLED and is_not_found_in_document(answer_text):
        offer_web_search = True
        web_prompt = "Would you like me to search external web sources for this?"
        clean_refusal = "The uploaded document(s) do not contain information regarding this topic."
        answer_text = f"{clean_refusal}\n\n{web_prompt}"
        citations = []

    asst_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        sender="assistant",
        content=answer_text,
        citations=[c.model_dump() for c in citations]
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    return ChatMessageResponse(
        session_id=session_id,
        message_id=asst_msg.id,
        sender="assistant",
        content=asst_msg.content,
        citations=citations,
        offer_web_search=offer_web_search,
        web_search_prompt=web_prompt if offer_web_search else None,
        original_query=payload.message,
        created_at=asst_msg.created_at
    )


async def process_web_search_chat(db: AsyncSession, payload: WebSearchChatRequest) -> ChatMessageResponse:
    """Handles opt-in web search fallback query synthesis and response saving."""
    if not settings.WEB_SEARCH_ENABLED:
        raise SmartDocException("Web search is currently disabled in backend settings.", status_code=400)

    user = await document_service.get_or_create_dev_user(db)
    session_id = payload.session_id

    if not session_id:
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Web Search Q&A Session",
            document_ids=payload.document_ids or []
        )
        db.add(session)
        await db.commit()
        session_id = session.id

    logger.info(f"Executing web search fallback query for session '{session_id}'")
    web_result = await execute_web_search_and_synthesize(payload.message)

    web_citations = [
        WebCitationItem(
            title=c["title"],
            url=c["url"],
            snippet=c.get("snippet")
        ) for c in web_result.get("web_citations", [])
    ]

    asst_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        sender="assistant",
        content=web_result["answer"],
        citations=[]
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    return ChatMessageResponse(
        session_id=session_id,
        message_id=asst_msg.id,
        sender="assistant",
        content=asst_msg.content,
        citations=[],
        offer_web_search=False,
        is_web_result=True,
        web_citations=web_citations,
        original_query=payload.message,
        created_at=asst_msg.created_at
    )


async def get_session_history(db: AsyncSession, session_id: str) -> List[ChatMessage]:
    """Retrieve message history for a chat session."""
    stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())
