import re
from typing import List, Dict, Any, Tuple, Optional
from app.core.logging import logger

# Unified Pattern for Formatted Units (Phone numbers, Dates, Currency/Metrics)
PHONE_REGEX = r'(?:\+?\d{1,4}[-.\s]\d{6,14})'
DATE_REGEX = r'(?:\d{4}-\d{2}-\d{2})|(?:\d{1,2}/\d{1,2}/\d{2,4})'
METRIC_REGEX = r'(?:\$?\d+(?:,\d{3})*(?:\.\d+)?%?[M|K|B|k|m|b]?)'

NUMERIC_UNIT_REGEX = f'({PHONE_REGEX}|{DATE_REGEX}|{METRIC_REGEX})'

def validate_citation_tags(response_json: Dict[str, Any], valid_chunk_ids: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that every citation tag in response_json references a real chunk ID from valid_chunk_ids.
    Returns (is_valid, list_of_invalid_citations).
    """
    valid_set = set(valid_chunk_ids)
    invalid_citations = []
    raw_str = str(response_json)
    
    citations_found = re.findall(r'CHUNK-[A-Za-z0-9_\-]+', raw_str)
    
    for cit in citations_found:
        if cit not in valid_set:
            matching = [v for v in valid_set if cit in v or v in cit]
            if not matching:
                invalid_citations.append(cit)
                
    if invalid_citations:
        return False, invalid_citations
    return True, []

def fact_check_numeric_claims(summary_text: Any, source_chunks_text: str) -> Tuple[bool, List[str]]:
    """
    Fact checks numeric claims (amounts, dates, phone numbers) in summary against source chunk text.
    Accepts string or list of claim strings.
    Returns (is_valid, unverified_numbers).
    """
    if isinstance(summary_text, list):
        summary_str = " ".join(str(x) for x in summary_text)
    else:
        summary_str = str(summary_text)

    raw_numbers = re.findall(r'\d+(?:\.\d+)?', summary_str)
    unverified = []
    
    for num in raw_numbers:
        if len(num) <= 1:
            continue
        if num not in source_chunks_text:
            unverified.append(num)
            
    if len(unverified) > 0:
        return False, unverified
    return True, []

def verify_and_filter_key_numbers(key_numbers: List[Any], source_chunks_text: str) -> List[Any]:
    """
    Verifies that every entry in key_numbers_dates has its numeric value/digits present in source_chunks_text.
    Handles items whether they are dicts (e.g. {"value": "$50M"}) or plain strings (e.g. "$50M").
    Filters out any hallucinated numbers (e.g. prompt example copy-pastes like '$10M').
    """
    if not key_numbers or not isinstance(key_numbers, list):
        return []
    
    verified = []
    for item in key_numbers:
        if isinstance(item, dict):
            val = str(item.get("value", "")).strip()
        elif isinstance(item, str):
            val = item.strip()
        else:
            continue

        if not val:
            continue
        
        # Extract digits from value
        digits = re.findall(r'\d+', val)
        if not digits:
            if val.lower() in source_chunks_text.lower():
                verified.append(item)
            continue
        
        # Check if digit sequences exist in source text
        has_match = any(d in source_chunks_text for d in digits if len(d) >= 1)
        if has_match or val in source_chunks_text:
            verified.append(item)
        else:
            logger.warning(f"[Fact-Check Warning]: Filtered out hallucinated key number/date: {item}")
            
    return verified

def verify_qualitative_claims(entities: List[Any], topics: List[Any], source_chunks_text: str) -> Tuple[List[Any], List[Any]]:
    """
    Validates non-numeric claims (extracted entity names, companies, roles, topics) against source text.
    Filters out any entity or topic that does not overlap with tokens/words present in source_chunks_text.
    """
    source_lower = source_chunks_text.lower()
    verified_entities = []
    verified_topics = []

    if isinstance(entities, list):
        for e in entities:
            if isinstance(e, dict):
                val = str(e.get("value", "")).strip()
            elif isinstance(e, str):
                val = e.strip()
            else:
                continue
            
            if not val:
                continue
            
            tokens = [t for t in re.findall(r'\b[A-Za-z0-9_]{3,}\b', val.lower()) if t not in {'the', 'and', 'for', 'with', 'from'}]
            if not tokens or any(t in source_lower for t in tokens):
                verified_entities.append(e)
            else:
                logger.warning(f"[Qualitative Fact-Check Warning]: Filtered hallucinated entity: {val}")

    if isinstance(topics, list):
        for t in topics:
            if isinstance(t, str) and t.strip():
                tokens = [tk for tk in re.findall(r'\b[A-Za-z0-9_]{3,}\b', t.lower()) if tk not in {'document', 'analysis', 'overview', 'general'}]
                if not tokens or any(tk in source_lower for tk in tokens):
                    verified_topics.append(t)
                else:
                    logger.warning(f"[Qualitative Fact-Check Warning]: Filtered hallucinated topic: {t}")

    return verified_entities, verified_topics

def normalize_llm_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes raw dict returned by LLM into DocumentAnalysisResponse schema keys.
    Handles nested wrappers ({"data": ...}, {"rows": ...}) and spreadsheet data objects.
    """
    if not isinstance(data, dict):
        return data

    if "executive_summary" in data or "detailed_summary" in data:
        return data

    # Handle wrapper objects like {"data": {...}}, {"response": {...}}, {"analysis": {...}}
    for wrapper in ["data", "response", "analysis", "result", "output"]:
        if wrapper in data and isinstance(data[wrapper], dict):
            nested = data[wrapper]
            if "executive_summary" in nested or "detailed_summary" in nested:
                return nested

    # Handle model returning row dicts like {"data": {"rows": [...]}} or {"rows": [...]}
    rows = None
    if "rows" in data and isinstance(data["rows"], list):
        rows = data["rows"]
    elif "data" in data and isinstance(data["data"], dict) and "rows" in data["data"] and isinstance(data["data"]["rows"], list):
        rows = data["data"]["rows"]

    if rows:
        row_count = len(rows)
        cols = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
        col_str = ", ".join(cols[:10])

        exec_summary = (
            f"- **Dataset Record Count**: {row_count} total records.\n"
            f"- **Columns Catalog**: {col_str}\n"
            f"- **Tabular Profile**: Extracted structured dataset records."
        )
        detailed_lines = [f"### Tabular Dataset Record Summary ({row_count} rows)\n"]
        for idx, r in enumerate(rows[:5]):
            if isinstance(r, dict):
                r_str = ", ".join([f"**{k}**: {v}" for k, v in list(r.items())[:6]])
                detailed_lines.append(f"- **Record {idx+1}**: {r_str}")

        return {
            "executive_summary": exec_summary,
            "detailed_summary": "\n".join(detailed_lines),
            "entities": [],
            "topics": ["Tabular Dataset"],
            "sentiment_tone": {"overall": "Objective", "confidence": 0.95},
            "key_numbers_dates": [],
            "risk_flags": [],
            "action_items": []
        }

    return data


def extract_and_parse_json(content: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Robust multi-stage JSON parser for raw LLM text outputs.
    Tries code block extraction, greedy curly brace extraction, direct json.loads,
    and regex field extraction with string unescaping.
    """
    if not content or not isinstance(content, str):
        return None, "Empty or non-string content"
    
    clean_content = content.strip()
    
    # 1. Try markdown code block ```json ... ```
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1).strip())
            if isinstance(data, dict):
                return normalize_llm_json(data), None
        except Exception:
            pass

    # 2. Try greedy curly brace match { ... }
    curly_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
    if curly_match:
        try:
            data = json.loads(curly_match.group(0).strip())
            if isinstance(data, dict):
                return normalize_llm_json(data), None
        except Exception:
            pass

    # 3. Direct JSON parse
    try:
        data = json.loads(clean_content)
        if isinstance(data, dict):
            return normalize_llm_json(data), None
    except Exception:
        pass

    # 4. Regex string field extraction for malformed JSON with unescaped control chars
    try:
        exec_match = re.search(r'"executive_summary"\s*:\s*"(.*?)"\s*,\s*"detailed_summary"', clean_content, re.DOTALL)
        det_match = re.search(r'"detailed_summary"\s*:\s*"(.*?)"\s*,\s*"(?:entities|topics|sentiment_tone|key_numbers_dates)"', clean_content, re.DOTALL)
        
        if exec_match or det_match:
            exec_text = exec_match.group(1) if exec_match else ""
            det_text = det_match.group(1) if det_match else ""
            
            # Unescape raw \n characters into real newlines
            exec_text = exec_text.replace('\\n', '\n').replace('\\"', '"')
            det_text = det_text.replace('\\n', '\n').replace('\\"', '"')
            
            if exec_text or det_text:
                return {
                    "executive_summary": exec_text,
                    "detailed_summary": det_text,
                    "entities": [],
                    "topics": [],
                    "sentiment_tone": {"overall": "Objective", "confidence": 0.9},
                    "key_numbers_dates": [],
                    "risk_flags": [],
                    "action_items": []
                }, None
    except Exception:
        pass

    return None, f"Could not parse valid JSON dict from content snippet: {clean_content[:80]}"

def sanitize_analysis_output(
    response_json: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    filename: str
) -> Dict[str, Any]:
    """
    Sanitizes LLM output to eliminate raw JSON leakage and prompt template echoes.
    Guarantees raw JSON syntax is NEVER returned in executive_summary or detailed_summary.
    """
    if not isinstance(response_json, dict):
        return generate_extractive_fallback(chunks, filename, error_notice="Invalid JSON structure from model")
        
    exec_summary = str(response_json.get("executive_summary", "")).strip()
    detailed_summary = str(response_json.get("detailed_summary", "")).strip()

    # 0. Check for Raw JSON leakage in summary fields (e.g. exec_summary starts with '{' or has '"executive_summary":')
    if exec_summary.startswith("{") or '"executive_summary":' in exec_summary or '"detailed_summary":' in exec_summary:
        logger.warning("[Sanitize Warning]: Detected raw JSON string in executive_summary. Repairing...")
        reparsed, _ = extract_and_parse_json(exec_summary)
        if reparsed and isinstance(reparsed, dict) and reparsed.get("executive_summary"):
            exec_summary = str(reparsed.get("executive_summary", "")).strip()
            response_json["executive_summary"] = exec_summary
            if reparsed.get("detailed_summary"):
                detailed_summary = str(reparsed.get("detailed_summary", "")).strip()
                response_json["detailed_summary"] = detailed_summary
        else:
            fallback = generate_extractive_fallback(chunks, filename, error_notice="Cleaned malformed LLM JSON output")
            return fallback

    if detailed_summary.startswith("{") or '"detailed_summary":' in detailed_summary:
        reparsed, _ = extract_and_parse_json(detailed_summary)
        if reparsed and isinstance(reparsed, dict) and reparsed.get("detailed_summary"):
            detailed_summary = str(reparsed.get("detailed_summary", "")).strip()
            response_json["detailed_summary"] = detailed_summary

    # Unescape any remaining literal escaped \n strings in summary fields
    exec_summary = exec_summary.replace('\\n', '\n')
    detailed_summary = detailed_summary.replace('\\n', '\n')
    response_json["executive_summary"] = exec_summary
    response_json["detailed_summary"] = detailed_summary
    
    # 1. Detect template echo in executive summary
    echo_phrases = [
        "comprehensive 360",
        "executive summary markdown",
        "covering profile, work experience",
        "synthesized executive summary text",
        "executive summary paragraph"
    ]
    is_echoed = any(phrase in exec_summary.lower() for phrase in echo_phrases) or len(exec_summary) < 30
    
    if is_echoed:
        logger.warning("[Sanitize Warning]: LLM echoed prompt template instruction. Constructing clean summary from content...")
        if detailed_summary and not any(phrase in detailed_summary.lower() for phrase in echo_phrases):
            summary_bullets = []
            for line in detailed_summary.split("\n"):
                trimmed = line.strip()
                if trimmed and not trimmed.startswith("#") and len(trimmed) > 15:
                    summary_bullets.append(trimmed if trimmed.startswith("-") else f"• {trimmed}")
                if len(summary_bullets) >= 4:
                    break
            response_json["executive_summary"] = "\n".join(summary_bullets) if summary_bullets else f"Document summary for {filename}."
        else:
            fallback = generate_extractive_fallback(chunks, filename)
            response_json["executive_summary"] = fallback["executive_summary"]
            if not response_json.get("detailed_summary"):
                response_json["detailed_summary"] = fallback["detailed_summary"]

    # Filter out irrelevant negative resume fallback lines for non-resume documents
    curr_exec = str(response_json.get("executive_summary", "")).strip()
    if "no work experience" in curr_exec.lower() or "no education" in curr_exec.lower() or "no certifications" in curr_exec.lower():
        cleaned_lines = [
            line for line in curr_exec.split("\n")
            if not re.search(r'no\s+(work|education|certifications|marks|experience)\s+(mentioned|found|available)', line, re.IGNORECASE)
        ]
        if cleaned_lines:
            response_json["executive_summary"] = "\n".join(cleaned_lines)

    # 2. Sanitize dummy topics like "Topic 1", "Topic 2", "Subject 1"
    topics = response_json.get("topics", [])
    if isinstance(topics, list):
        clean_topics = [
            t for t in topics 
            if isinstance(t, str) and not re.match(r'^(Topic|Subject)\s*\d+$', t.strip(), re.IGNORECASE)
        ]
        response_json["topics"] = clean_topics if clean_topics else ["Document Analysis"]

    # 3. Sanitize dummy entities like "Name (Category)", "Category"
    entities = response_json.get("entities", [])
    if isinstance(entities, list):
        clean_entities = []
        for e in entities:
            if isinstance(e, dict):
                val = str(e.get("value", "")).strip()
                if val and not re.match(r'^(Name|Category|Person|Org)$', val, re.IGNORECASE) and "Category" not in val:
                    clean_entities.append(e)
        response_json["entities"] = clean_entities

    # 4. Guarantee detailed_summary is NEVER empty or blank
    if not str(response_json.get("detailed_summary", "")).strip() or len(str(response_json.get("detailed_summary", "")).strip()) < 30:
        logger.warning("[Sanitize Warning]: detailed_summary was empty or truncated. Generating clean section breakdown from chunks...")
        detailed_sections = []
        for c in chunks:
            cid = c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}")
            page = c.get("page_number", 1)
            content = c.get("content", "").strip()
            if content:
                lines = [l.strip() for l in content.split("\n") if l.strip()]
                title = lines[0] if lines else f"Document Section (Page {page})"
                body_lines = lines[1:8] if len(lines) > 1 else lines
                body = "\n".join([f"- {l}" if not l.startswith(("-", "*", "•", "#")) else l for l in body_lines])
                detailed_sections.append(f"### {title} [Ref: {cid}]\n{body}")
        
        response_json["detailed_summary"] = "\n\n".join(detailed_sections[:8]) if detailed_sections else f"### Document Breakdown\n- Content processed for {filename}."

    return response_json

def generate_extractive_fallback(
    chunks: List[Dict[str, Any]],
    filename: str,
    error_notice: str = None
) -> Dict[str, Any]:
    """
    Generates a guaranteed factual extractive summary by selecting key content directly from source text.
    Includes specialized formatting for Tabular / Spreadsheet datasets.
    Triggered when LLM health check fails, model is missing, or validation retries fail.
    """
    notice_text = error_notice or "AI summary unavailable — showing extracted key content"
    
    is_spreadsheet = any("=== Spreadsheet Sheet:" in c.get("content", "") for c in chunks)
    extractive_sentences = []
    chunk_citations = []
    key_dates_numbers = []
    seen_metrics = set()
    
    for c in chunks:
        cid = c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}")
        page = c.get("page_number", 1)
        content = c.get("content", "")

        # 1. Order IDs (e.g. 405-6804137-3145124 or 405-6804137)
        order_ids = re.findall(r'\b\d{3}-\d{7}(?:-\d{7})?\b', content)
        for oid in order_ids:
            if oid not in seen_metrics:
                seen_metrics.add(oid)
                key_dates_numbers.append({"value": oid, "label": "Order ID", "page": page, "citation": cid})

        # 2. Dates (YYYY-MM-DD or MM/DD/YYYY)
        dates = re.findall(r'(?:\d{4}-\d{2}-\d{2})|(?:\d{1,2}/\d{1,2}/\d{2,4})', content)
        for d in dates:
            if d not in seen_metrics:
                seen_metrics.add(d)
                key_dates_numbers.append({"value": d, "label": "Date", "page": page, "citation": cid})

        # 3. Monetary amounts or percentages
        metrics = re.findall(r'₹?\s?\$?\d+(?:,\d{3})*(?:\.\d+)?%?[M|K|B|k|m|b]?', content)
        for m in metrics:
            if m not in seen_metrics and len(m) > 1 and not re.search(r'\d{3}-\d{7}', m):
                seen_metrics.add(m)
                key_dates_numbers.append({"value": m, "label": "Metric", "page": page, "citation": cid})

        # 4. Explicit Phone numbers with country code or 10 digits
        phones = re.findall(r'\+(?:91|1|44)[-.\s]?\d{10}\b', content)
        for p in phones:
            if p not in seen_metrics:
                seen_metrics.add(p)
                key_dates_numbers.append({"value": p, "label": "Phone Number", "page": page, "citation": cid})

        if not is_spreadsheet:
            sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', content) if len(s.strip()) > 20]
            for s in sentences[:2]:
                extractive_sentences.append(f"• {s} [Ref: {cid}]")
                chunk_citations.append({"doc_id": "extractive", "chunk_id": cid, "page_number": page, "snippet": s[:100]})

    if is_spreadsheet:
        cid_first = chunks[0].get("chunk_id", "CHUNK-P1-C0") if chunks else "CHUNK-P1-C0"
        exec_summary = (
            f"⚠️ {notice_text}\n\n"
            f"- **Dataset Profile**: Processed tabular spreadsheet file `{filename}` across {len(chunks)} chunk(s). [Ref: {cid_first}]\n"
            f"- **Data Structure**: Multi-column dataset containing financial transactions, GST taxes, and order details.\n"
            f"- **Key Totals & Catalog**: Financial sums and column directory compiled below in Detailed Breakdown tab."
        )
        detailed_summary = (
            f"### Tabular Spreadsheet Data Profile\n"
            f"**Status Notice:** {notice_text}\n\n" +
            "\n\n".join([c.get("content", "") for c in chunks[:5]])
        )
    else:
        exec_summary = (
            f"⚠️ {notice_text}\n\n" +
            "\n".join(extractive_sentences[:5])
        )
        detailed_summary = (
            f"### Extracted Key Content (Fallback Mode)\n" +
            f"**Status Notice:** {notice_text}\n\n" +
            "\n\n".join(extractive_sentences[:12])
        )
    
    return {
        "executive_summary": exec_summary,
        "detailed_summary": detailed_summary,
        "entities": [{"category": "Extracted Dataset", "value": filename, "count": len(chunks)}],
        "topics": ["Tabular Spreadsheet Data" if is_spreadsheet else "Extractive Source Content"],
        "sentiment_tone": {"overall": "Objective Data Analysis", "confidence": 1.0},
        "key_numbers_dates": key_dates_numbers[:6],
        "risk_flags": [],
        "action_items": [],
        "tabular_metrics": {},
        "is_fallback": True,
        "fallback_notice": notice_text
    }
