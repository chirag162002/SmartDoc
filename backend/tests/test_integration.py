import pytest
import asyncio
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import sync_engine, Base
from app.services.task_runner import process_document_background

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=sync_engine)

@pytest.mark.asyncio
async def test_full_document_pipeline_integration(tmp_path):
    """
    True end-to-end integration test:
    1. Upload document file via API endpoint (/api/v1/documents/upload)
    2. Run background processing pipeline (task_runner process_document_background)
    3. Retrieve status (/api/v1/documents/{id}/status) and assert status == COMPLETE
    4. Retrieve analysis (/api/v1/analysis/{id}) and assert structured output (executive_summary, entities, risk_flags)
    5. Perform grounded chat query (/api/v1/chat/message) and verify grounded answer format
    """
    # 1. Prepare sample document file
    sample_file = tmp_path / "integration_sample.txt"
    sample_file.write_text(
        "Quarterly Financial & Operational Report - Q3 2026\n\n"
        "Executive Summary:\n"
        "Acme Global Inc achieved $5.2M in Revenue with 22% Net Operating Margin during Q3 2026.\n"
        "Key Milestone: Launched cloud migration initiative ahead of schedule.\n"
        "Risk Assessment: Supply chain delay in regional logistics center identified as Medium Risk.\n"
        "Action Item: Audit vendor compliance by end of October 2026."
    )

    # 2. Upload document via API
    with open(sample_file, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("integration_sample.txt", f, "text/plain")}
        )
    
    assert response.status_code == 202
    upload_data = response.json()
    doc_id = upload_data["id"]
    assert doc_id is not None
    assert upload_data["original_name"] == "integration_sample.txt"

    # 3. Execute background processing task explicitly for test verification
    with patch("app.services.llm_provider.OllamaProvider.check_ollama_health", return_value=(False, "Mocked offline")):
        await process_document_background(doc_id)

    # 4. Fetch document status via API
    status_res = client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "COMPLETE"
    assert status_data["progress_percent"] == 100

    # 5. Retrieve complete document analysis
    analysis_res = client.get(f"/api/v1/analysis/{doc_id}")
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()

    assert analysis_data["document_id"] == doc_id
    assert "executive_summary" in analysis_data
    assert len(analysis_data["executive_summary"]) > 0
    assert "detailed_summary" in analysis_data
    assert "key_numbers_dates" in analysis_data
    assert "risk_flags" in analysis_data

    # 6. Test Grounded Chat query
    with patch("app.services.chat_service.answer_document_query") as mock_answer:
        mock_answer.return_value = {
            "answer": "Acme Global Inc reported $5.2M in Revenue during Q3 2026. [Ref: CHUNK-1-Page-1]",
            "citations": [{"doc_id": doc_id, "chunk_id": "CHUNK-1-P1-C0", "page_number": 1, "snippet": "Acme Global Inc achieved $5.2M"}]
        }
        chat_res = client.post(
            "/api/v1/chat/message",
            json={
                "document_ids": [doc_id],
                "message": "What was the revenue reported in Q3 2026?"
            }
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "content" in chat_data
        assert "session_id" in chat_data
