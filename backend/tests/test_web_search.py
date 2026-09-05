import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.services.chat_service import is_not_found_in_document
from app.services.web_search_service import execute_web_search_and_synthesize, search_tavily
from app.core.config import settings

def test_is_not_found_in_document():
    refusal_msg1 = "The uploaded document(s) do not contain information regarding quantum computing."
    refusal_msg2 = "This topic is not covered in the document."
    refusal_msg3 = "The document does not mention any financial revenue."
    valid_answer = "### Work Experience\n- Software Engineer at Acme Corp [Ref: CHUNK-1-Page-1]"

    assert is_not_found_in_document(refusal_msg1) is True
    assert is_not_found_in_document(refusal_msg2) is True
    assert is_not_found_in_document(refusal_msg3) is True
    assert is_not_found_in_document(valid_answer) is False

from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_search_tavily_mock():
    mock_response = {
        "results": [
            {
                "title": "Quantum Computing Overview",
                "url": "https://example.com/quantum",
                "content": "Quantum computing uses qubits to perform complex computations."
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response
        mock_post.return_value = mock_res
        
        results = await search_tavily("quantum computing", "test_key")
        assert len(results) == 1
        assert results[0]["title"] == "Quantum Computing Overview"
        assert results[0]["url"] == "https://example.com/quantum"


@pytest.mark.asyncio
async def test_web_search_fallback_when_no_results():
    with patch("app.services.web_search_service.search_tavily", return_value=[]), \
         patch("app.services.web_search_service.search_duckduckgo_fallback", return_value=[]):
        res = await execute_web_search_and_synthesize("non_existent_query_xyz_123")
        assert "Web search didn't return results" in res["answer"]
        assert res["web_citations"] == []
