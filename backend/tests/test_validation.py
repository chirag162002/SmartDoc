import pytest
from app.services.llm_validation import (
    validate_citation_tags,
    fact_check_numeric_claims,
    verify_and_filter_key_numbers,
    verify_qualitative_claims,
    sanitize_analysis_output
)

def test_citation_validation_valid_and_invalid():
    """Verify citation validation accepts real chunk IDs and rejects nonexistent chunk IDs."""
    valid_ids = ["CHUNK-doc1-P1-C0", "CHUNK-doc1-P1-C1"]
    
    # Valid output
    valid_json = {
        "executive_summary": "Summary text [Ref: CHUNK-doc1-P1-C0].",
        "detailed_summary": "Details [Ref: CHUNK-doc1-P1-C1]."
    }
    is_valid, invalid_tags = validate_citation_tags(valid_json, valid_ids)
    assert is_valid is True
    assert len(invalid_tags) == 0

    # Output referencing nonexistent chunk ID
    invalid_json = {
        "executive_summary": "Summary text referencing fake chunk [Ref: CHUNK-999-FAKE-P10-C5]."
    }
    is_valid_fake, invalid_tags_fake = validate_citation_tags(invalid_json, valid_ids)
    assert is_valid_fake is False
    assert "CHUNK-999-FAKE-P10-C5" in invalid_tags_fake or any("CHUNK-999" in tag for tag in invalid_tags_fake)


def test_numeric_fact_checking_rejects_hallucinated_number():
    """
    Verify numeric fact-checking logic correctly rejects fabricated numbers
    NOT present in source text (specifically testing the $10M Revenue hallucination bug).
    """
    source_text = "The company reported Total Income of $2.5M for Fiscal Year 2025 and 15% YoY Growth."

    key_numbers_input = [
        {"value": "$2.5M", "label": "Total Income"},
        {"value": "15%", "label": "YoY Growth"},
        {"value": "$10M", "label": "Fabricated Revenue Hallucination"},  # NOT in source!
        {"value": "99.99%", "label": "Unmentioned Metric"}  # NOT in source!
    ]

    verified = verify_and_filter_key_numbers(key_numbers_input, source_text)

    values = [item["value"] for item in verified]
    assert "$2.5M" in values
    assert "15%" in values
    # Must reject fabricated $10M Revenue and 99.99%!
    assert "$10M" not in values
    assert "99.99%" not in values


def test_fact_check_numeric_claims_general():
    """Verify general numeric claims fact-checker detects ungrounded numbers."""
    source_text = "Project duration is 14 Weeks with a target budget of $50,000."
    valid_summary = "The duration is 14 Weeks and budget is $50,000."
    hallucinated_summary = "The duration is 14 Weeks and budget is $100,000."

    is_valid_1, unverified_1 = fact_check_numeric_claims(valid_summary, source_text)
    assert is_valid_1 is True
    assert len(unverified_1) == 0

    is_valid_2, unverified_2 = fact_check_numeric_claims(hallucinated_summary, source_text)
    assert is_valid_2 is False
    assert "100" in unverified_2 or "100000" in unverified_2


def test_verify_qualitative_claims():
    """Verify entity and topic filtering against source text."""
    source = "Acme Corp announced partnership with BetaTech for AI analytics platform."
    entities = [
        {"category": "Organization", "value": "Acme Corp"},
        {"category": "Organization", "value": "Zeta Global Fake Company"}
    ]
    topics = ["AI analytics", "Underwater Basket Weaving"]

    v_entities, v_topics = verify_qualitative_claims(entities, topics, source)
    
    entity_vals = [e["value"] for e in v_entities]
    assert "Acme Corp" in entity_vals
    assert "Zeta Global Fake Company" not in entity_vals

    assert "AI analytics" in v_topics
    assert "Underwater Basket Weaving" not in v_topics


def test_sanitize_analysis_output():
    """Verify raw JSON repair and prompt echo removal."""
    raw_response = {
        "executive_summary": "Comprehensive 360-degree executive summary covering profile...",
        "detailed_summary": "### Section 1\n- Core contract terms.",
        "topics": ["Topic 1", "Real Estate"],
        "entities": [{"category": "Org", "value": "Real Estate Inc"}]
    }
    chunks = [{"chunk_id": "CHUNK-1", "page_number": 1, "content": "Real Estate Inc contract terms."}]
    sanitized = sanitize_analysis_output(raw_response, chunks, "test.pdf")

    assert "Comprehensive 360" not in sanitized["executive_summary"]
    assert "Topic 1" not in sanitized["topics"]
    assert "Real Estate" in sanitized["topics"]
