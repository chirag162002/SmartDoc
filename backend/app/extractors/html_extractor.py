import trafilatura
import httpx
from typing import Dict, Any

def extract_html(file_path_or_url: str) -> Dict[str, Any]:
    try:
        if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
            # Web URL
            response = httpx.get(file_path_or_url, timeout=15.0, follow_redirects=True)
            html_content = response.text
        else:
            # Local HTML file
            with open(file_path_or_url, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
                
        extracted_text = trafilatura.extract(html_content, include_tables=True, include_links=False)
        if not extracted_text:
            extracted_text = "No readable main body content found in HTML document."
            
    except Exception as e:
        raise ValueError(f"Failed to fetch or parse HTML content: {str(e)}")

    page_count = max(1, len(extracted_text) // 3000)
    
    return {
        "file_type": "html",
        "page_count": page_count,
        "full_text": extracted_text,
        "pages": [{"page_number": 1, "text": extracted_text}],
        "is_tabular": False,
        "tabular_stats": {}
    }
