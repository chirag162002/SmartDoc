import pdfplumber
import pypdf
from typing import Dict, Any, List
from app.extractors.ocr_extractor import extract_pdf_ocr

def extract_pdf(file_path: str) -> Dict[str, Any]:
    pages = []
    full_text_parts = []
    page_count = 0
    
    try:
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for idx, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                tables = page.extract_tables() or []
                
                # Format tables into readable text if present
                table_texts = []
                for table in tables:
                    for row in table:
                        row_filtered = [str(cell) for cell in row if cell is not None]
                        if row_filtered:
                            table_texts.append(" | ".join(row_filtered))
                
                combined_text = page_text
                if table_texts:
                    combined_text += "\n\n[Tables Found on Page " + str(idx + 1) + "]:\n" + "\n".join(table_texts)
                
                pages.append({
                    "page_number": idx + 1,
                    "text": combined_text,
                    "tables": tables
                })
                full_text_parts.append(f"--- Page {idx + 1} ---\n{combined_text}")
    except Exception:
        # Fallback to pypdf
        try:
            reader = pypdf.PdfReader(file_path)
            page_count = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                pages.append({
                    "page_number": idx + 1,
                    "text": txt,
                    "tables": []
                })
                full_text_parts.append(f"--- Page {idx + 1} ---\n{txt}")
        except Exception as e:
            # Physical failure or severe corruption
            raise ValueError(f"Unable to parse PDF file. File may be encrypted or corrupted. Detail: {str(e)}")

    full_text = "\n\n".join(full_text_parts)
    
    # Check if scanned PDF (average text length per page < 50 chars)
    avg_chars = len(full_text.strip()) / max(1, page_count)
    if avg_chars < 50:
        # Trigger OCR Fallback
        return extract_pdf_ocr(file_path, page_count)

    return {
        "file_type": "pdf",
        "page_count": page_count,
        "full_text": full_text,
        "pages": pages,
        "is_tabular": False,
        "tabular_stats": {}
    }
