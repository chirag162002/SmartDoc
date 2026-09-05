import math
from typing import List, Dict, Any

def chunk_document_pages(
    doc_id: str,
    pages: List[Dict[str, Any]],
    chunk_size_chars: int = 4000,
    overlap_chars: int = 400
) -> List[Dict[str, Any]]:
    """
    Chunks document pages preserving page numbers and creating citation reference IDs.
    Returns list of chunk dicts:
    [
      {
        "chunk_id": "CHUNK-{doc_id}-P1-C0",
        "chunk_index": 0,
        "page_number": 1,
        "content": "...",
        "token_count": int
      }
    ]
    """
    chunks = []
    global_index = 0
    
    for page_info in pages:
        page_num = page_info.get("page_number", 1)
        text = page_info.get("text", "").strip()
        if not text:
            continue
            
        if len(text) <= chunk_size_chars:
            chunks.append({
                "chunk_id": f"CHUNK-{doc_id[:8]}-P{page_num}-C{global_index}",
                "chunk_index": global_index,
                "page_number": page_num,
                "content": text,
                "token_count": max(1, len(text) // 4)
            })
            global_index += 1
        else:
            # Sub-chunk long pages with overlap
            start = 0
            while start < len(text):
                end = min(start + chunk_size_chars, len(text))
                chunk_str = text[start:end]
                chunks.append({
                    "chunk_id": f"CHUNK-{doc_id[:8]}-P{page_num}-C{global_index}",
                    "chunk_index": global_index,
                    "page_number": page_num,
                    "content": chunk_str,
                    "token_count": max(1, len(chunk_str) // 4)
                })
                global_index += 1
                if end >= len(text):
                    break
                start += (chunk_size_chars - overlap_chars)
                
    return chunks
