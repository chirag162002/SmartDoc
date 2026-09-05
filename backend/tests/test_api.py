import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import sync_engine, Base

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=sync_engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_documents():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_text_file(tmp_path):
    test_file_path = tmp_path / "sample_contract.txt"
    test_file_path.write_text("Master Service Agreement between Company A and Company B. Effective Date: September 2026. Payment terms: Net 30 days. Risk Clause: Uncapped liability.")
    
    with open(test_file_path, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample_contract.txt", f, "text/plain")}
        )
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["original_name"] == "sample_contract.txt"
    assert data["status"] in ["PENDING", "EXTRACTING", "COMPLETE"]
