from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size_bytes: int
    status: str
    progress_percent: int
    current_stage: str
    error_message: Optional[str] = None
    page_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    progress_percent: int
    current_stage: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class EntityItem(BaseModel):
    category: str
    value: str
    count: int = 1

class RiskFlagItem(BaseModel):
    risk: str
    severity: str  # HIGH, MEDIUM, LOW
    citation: Optional[str] = None
    description: Optional[str] = None

class ActionItem(BaseModel):
    item: str
    priority: Optional[str] = "MEDIUM"
    owner: Optional[str] = None

class KeyNumberDateItem(BaseModel):
    value: str
    label: str
    page: Optional[int] = None
    citation: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    document_id: str
    executive_summary: str
    detailed_summary: str
    entities: List[Dict[str, Any]] = []
    topics: List[str] = []
    sentiment_tone: Dict[str, Any] = {}
    key_numbers_dates: List[Dict[str, Any]] = []
    risk_flags: List[Dict[str, Any]] = []
    action_items: List[Dict[str, Any]] = []
    tabular_metrics: Dict[str, Any] = {}
    is_fallback: Optional[bool] = False
    fallback_notice: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ComparisonRequest(BaseModel):
    document_ids: List[str]

class ComparisonItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    executive_summary: str
    key_metrics: List[str]
    top_risks: List[str]

class ComparisonResponse(BaseModel):
    comparative_summary: str
    key_differences: List[str]
    matrix: List[ComparisonItem]

class ChatMessageRequest(BaseModel):
    session_id: Optional[str] = None
    document_ids: List[str]
    message: str

class CitationItem(BaseModel):
    doc_id: str
    chunk_id: str
    page_number: Optional[int] = None
    snippet: str

class WebCitationItem(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None

class WebSearchChatRequest(BaseModel):
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = []
    message: str

class ChatMessageResponse(BaseModel):
    session_id: str
    message_id: str
    sender: str
    content: str
    citations: List[CitationItem] = []
    offer_web_search: bool = False
    web_search_prompt: Optional[str] = None
    is_web_result: bool = False
    web_citations: List[WebCitationItem] = []
    original_query: Optional[str] = None
    created_at: datetime


class ChatMessageHistoryItem(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    citations: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True

