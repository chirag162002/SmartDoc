from typing import List, Dict, Any
from app.services.llm_provider import get_llm_provider

async def process_map_reduce_analysis(
    doc_id: str,
    filename: str,
    chunks: List[Dict[str, Any]],
    is_tabular: bool = False,
    tabular_stats: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Executes document analysis pipeline via configured LLMProvider (Ollama or Claude).
    Enforces strict grounding and source citation tags [Ref: CHUNK-id-Page-N].
    """
    provider = get_llm_provider()
    return await provider.summarize(
        chunks=chunks,
        filename=filename,
        is_tabular=is_tabular,
        tabular_stats=tabular_stats
    )
