from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.document import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageHistoryItem,
    WebSearchChatRequest
)
from app.services import chat_service

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(payload: ChatMessageRequest, db: AsyncSession = Depends(get_db)) -> ChatMessageResponse:
    """Send follow-up question in chat-with-document mode. Returns grounded answer with chunk citations."""
    return await chat_service.process_chat_message(db, payload)

@router.post("/web-search", response_model=ChatMessageResponse)
async def execute_web_search_chat(payload: WebSearchChatRequest, db: AsyncSession = Depends(get_db)) -> ChatMessageResponse:
    """
    Opt-in web search fallback endpoint. Triggers live external web search,
    synthesizes cited answer, and saves assistant response.
    """
    return await chat_service.process_web_search_chat(db, payload)

@router.get("/sessions/{session_id}/history", response_model=List[ChatMessageHistoryItem])
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)) -> List[ChatMessageHistoryItem]:
    """Fetch message history for a chat session."""
    history = await chat_service.get_session_history(db, session_id)
    return [ChatMessageHistoryItem.model_validate(item) for item in history]
