import pytest
import asyncio
from unittest.mock import patch
from app.services.llm_provider import OllamaProvider, ClaudeProvider, get_llm_provider
from app.services.llm_validation import validate_citation_tags, fact_check_numeric_claims, generate_extractive_fallback

@pytest.mark.asyncio
async def test_llm_provider_factory():
    provider = get_llm_provider()
    assert provider is not None
    assert isinstance(provider, (OllamaProvider, ClaudeProvider))

def test_citation_validation():
    valid_chunks = ["CHUNK-doc-P1-C0", "CHUNK-doc-P1-C1"]
    
    # Valid output
    valid_json = {
        "executive_summary": "Company reported $10M revenue [Ref: CHUNK-doc-P1-C0]."
    }
    is_valid, invalid = validate_citation_tags(valid_json, valid_chunks)
    assert is_valid is True
    assert len(invalid) == 0
    
    # Invalid output referencing fake chunk
    invalid_json = {
        "executive_summary": "Fake summary [Ref: CHUNK-fake-P99-C99]."
    }
    is_valid, invalid = validate_citation_tags(invalid_json, valid_chunks)
    assert is_valid is False
    assert "CHUNK-fake-P99-C99" in invalid

def test_fact_check_numeric_claims():
    source_text = "The company reported $45.2M in Q3 2026 revenue with 15% growth."
    
    # Accurate summary
    accurate_summary = "Revenue was $45.2M in Q3 with 15% growth."
    is_valid, unverified = fact_check_numeric_claims(accurate_summary, source_text)
    assert is_valid is True
    
    # Hallucinated summary with fake numbers
    hallucinated_summary = "Revenue was $999.9M in Q3 with 88% growth."
    is_valid, unverified = fact_check_numeric_claims(hallucinated_summary, source_text)
    assert len(unverified) > 0

def test_extractive_fallback():
    chunks = [
        {"chunk_id": "CHUNK-doc-P1-C0", "page_number": 1, "content": "Master Service Agreement signed in September 2026. Payment terms are Net 30 days."}
    ]
    fallback_res = generate_extractive_fallback(chunks, "contract.pdf")
    assert fallback_res["is_fallback"] is True
    assert "showing extracted key" in fallback_res["executive_summary"]
    assert "Master Service Agreement" in fallback_res["detailed_summary"]

@pytest.mark.asyncio
async def test_provider_regression_diff():
    """Runs test document through both providers when available to diff outputs."""
    sample_chunks = [
        {"chunk_id": "CHUNK-doc-P1-C0", "page_number": 1, "content": "Financial statement Q3 2026: Revenue $50M, Net Income $12M."}
    ]
    
    ollama = OllamaProvider()
    claude = ClaudeProvider()
    
    with patch.object(ollama, "check_ollama_health", return_value=(False, "Mocked offline")):
        res_ollama = await ollama.summarize(sample_chunks, "test_finances.pdf")
        assert "executive_summary" in res_ollama
    
    res_claude = await claude.summarize(sample_chunks, "test_finances.pdf")
    assert "executive_summary" in res_claude

def test_extract_and_parse_json_and_sanitization():
    from app.services.llm_validation import extract_and_parse_json, sanitize_analysis_output
    
    # 1. Test malformed JSON with escaped backslashes
    raw_content = '{\n  "executive_summary": "Chirag Maheshwari is an AI engineer\\nWith hands on experience.",\n  "detailed_summary": "### Profile\\n- Details"\n}'
    parsed, err = extract_and_parse_json(raw_content)
    assert parsed is not None
    assert "Chirag Maheshwari" in parsed["executive_summary"]
    assert err is None
    
    # 2. Test raw JSON string embedded inside executive_summary field
    raw_json_embedded = {
        "executive_summary": '{\n  "executive_summary": "Clean summary text",\n  "detailed_summary": "### Clean Section\\n- Detail"\n}',
        "detailed_summary": ""
    }
    chunks = [{"chunk_id": "CHUNK-1", "page_number": 1, "content": "Clean sample document content"}]
    sanitized = sanitize_analysis_output(raw_json_embedded, chunks, "test.pdf")
    assert not sanitized["executive_summary"].startswith("{")
    assert "Clean summary text" in sanitized["executive_summary"] or "Clean sample document" in sanitized["executive_summary"]
