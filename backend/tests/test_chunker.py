import pytest
from app.services.chunker import chunk_document_pages

def test_chunking_single_page_short():
    """Verify small page text produces a single chunk with correct metadata."""
    pages = [
        {"page_number": 1, "text": "This is a short single-page document test."}
    ]
    chunks = chunk_document_pages("doc123", pages)

    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert "CHUNK-doc123-P1-C0" in chunks[0]["chunk_id"]
    assert "short single-page" in chunks[0]["content"]


def test_chunking_multi_page_large():
    """Verify large multi-page document produces multiple chunks with boundaries preserved."""
    long_text_p1 = "Paragraph 1: " + ("SmartDoc document intelligence system text content. " * 100)
    long_text_p2 = "Paragraph 2: " + ("Second page detailed analytics summary breakdown. " * 100)

    pages = [
        {"page_number": 1, "text": long_text_p1},
        {"page_number": 2, "text": long_text_p2}
    ]

    chunks = chunk_document_pages("doc_multi", pages, chunk_size_chars=1000, overlap_chars=100)

    assert len(chunks) > 1

    # Check page numbers and chunk_ids
    page_numbers = {c["page_number"] for c in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers

    # Verify chunk structure
    for c in chunks:
        assert "chunk_id" in c
        assert "content" in c
        assert "token_count" in c
        assert c["token_count"] > 0
        assert len(c["content"]) <= 1200  # Boundary within soft max limit


def test_chunking_empty_pages_handled():
    """Verify empty pages do not crash chunker."""
    pages = [
        {"page_number": 1, "text": ""},
        {"page_number": 2, "text": "   \n  \t  "},
        {"page_number": 3, "text": "Page 3 has real content."}
    ]
    chunks = chunk_document_pages("doc_empty", pages)
    assert len(chunks) >= 1
    assert any("Page 3" in c["content"] for c in chunks)
