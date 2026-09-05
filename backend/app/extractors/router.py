import os
import mimetypes
from typing import Dict, Any, List, Tuple
from app.extractors.pdf_extractor import extract_pdf
from app.extractors.docx_extractor import extract_docx
from app.extractors.excel_extractor import extract_excel
from app.extractors.pptx_extractor import extract_pptx
from app.extractors.ocr_extractor import extract_image_ocr
from app.extractors.html_extractor import extract_html

def detect_file_type(file_path: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    
    # Extension mapping
    if ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.docx', '.doc']:
        return 'docx'
    elif ext in ['.xlsx', '.xls', '.csv', '.tsv']:
        return 'excel'
    elif ext in ['.pptx', '.ppt']:
        return 'pptx'
    elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp']:
        return 'image'
    elif ext in ['.html', '.htm']:
        return 'html'
    elif ext in ['.txt', '.md', '.log', '.json']:
        return 'text'
    
    # Magic bytes check fallback
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)
            if header.startswith(b'%PDF'):
                return 'pdf'
            elif header.startswith(b'PK\x03\x04'):
                if 'docx' in filename:
                    return 'docx'
                elif 'pptx' in filename:
                    return 'pptx'
                elif 'xlsx' in filename:
                    return 'excel'
            elif header.startswith(b'\x89PNG') or header.startswith(b'\xff\xd8\xff'):
                return 'image'
    except Exception:
        pass
        
    return 'text'

def extract_document_content(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Routes document extraction based on detected file type.
    Returns normalized structure:
    {
      "file_type": str,
      "page_count": int,
      "full_text": str,
      "pages": [ {"page_number": int, "text": str, "tables": list} ],
      "is_tabular": bool,
      "tabular_stats": dict (if spreadsheet)
    }
    """
    file_type = detect_file_type(file_path, filename)
    
    if file_type == 'pdf':
        return extract_pdf(file_path)
    elif file_type == 'docx':
        return extract_docx(file_path)
    elif file_type == 'excel':
        return extract_excel(file_path, filename)
    elif file_type == 'pptx':
        return extract_pptx(file_path)
    elif file_type == 'image':
        return extract_image_ocr(file_path)
    elif file_type == 'html':
        return extract_html(file_path)
    else:
        # Plain text
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return {
            "file_type": "text",
            "page_count": max(1, len(text) // 3000),
            "full_text": text,
            "pages": [{"page_number": 1, "text": text}],
            "is_tabular": False,
            "tabular_stats": {}
        }
