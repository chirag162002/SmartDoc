import os
from typing import Dict, Any, List
from PIL import Image
import pytesseract

def extract_image_ocr(file_path: str) -> Dict[str, Any]:
    try:
        img = Image.open(file_path)
        ocr_text = pytesseract.image_to_string(img)
        if not ocr_text.strip():
            ocr_text = "[OCR Warning: Image contains no detectable text or low resolution content.]"
    except Exception as e:
        if "tesseract is not installed" in str(e).lower() or "tesseractnotfound" in type(e).__name__.lower():
            ocr_text = "[OCR Notice: Local Tesseract OCR binary is not installed on server environment. Image processed without text extraction.]"
        else:
            ocr_text = f"[OCR Extraction Error: {str(e)}]"

    return {
        "file_type": "image",
        "page_count": 1,
        "full_text": ocr_text,
        "pages": [{"page_number": 1, "text": ocr_text}],
        "is_tabular": False,
        "tabular_stats": {}
    }

def extract_pdf_ocr(file_path: str, page_count: int) -> Dict[str, Any]:
    pages = []
    full_text_parts = []
    
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=1, last_page=min(page_count, 10))
        for idx, img in enumerate(images):
            try:
                txt = pytesseract.image_to_string(img)
            except Exception:
                txt = f"[OCR Notice: Page {idx+1} could not be processed via local Tesseract OCR.]"
            
            pages.append({"page_number": idx + 1, "text": txt})
            full_text_parts.append(f"--- Page {idx + 1} (Scanned OCR) ---\n{txt}")
    except Exception as e:
        # Fallback message if pdf2image or poppler is missing
        placeholder = f"[Scanned PDF Notice: PDF appears to be image-based. Poppler/Tesseract OCR engine returned: {str(e)}]"
        return {
            "file_type": "pdf_scanned",
            "page_count": page_count,
            "full_text": placeholder,
            "pages": [{"page_number": 1, "text": placeholder}],
            "is_tabular": False,
            "tabular_stats": {}
        }

    full_text = "\n\n".join(full_text_parts)
    return {
        "file_type": "pdf_scanned",
        "page_count": len(pages),
        "full_text": full_text,
        "pages": pages,
        "is_tabular": False,
        "tabular_stats": {}
    }
