from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.services.llm_provider import OllamaProvider, ClaudeProvider

router = APIRouter()

class SystemStatusResponse(BaseModel):
    status: str
    provider: str
    model: str
    is_online: bool
    error_detail: Optional[str] = None

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """
    Returns active LLM provider configuration, model name, and live health status.
    Used by frontend header badge and system monitoring.
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "ollama":
        provider = OllamaProvider()
        is_online, error_detail = await provider.check_ollama_health()
        model_name = settings.OLLAMA_MODEL
    else:
        claude_provider = ClaudeProvider()
        is_online = await claude_provider.health_check()
        error_detail = None if is_online else "Anthropic API Key is missing or invalid."
        model_name = settings.DEFAULT_MODEL

    return SystemStatusResponse(
        status="healthy" if is_online else "degraded",
        provider=provider_name,
        model=model_name,
        is_online=is_online,
        error_detail=error_detail
    )
