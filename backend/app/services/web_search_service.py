import logging
import httpx
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime

from app.core.config import settings
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger("smartdoc.web_search")

async def search_tavily(query: str, api_key: str) -> List[Dict[str, str]]:
    """Perform web search using Tavily API."""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "max_results": 5
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", "Web Source"),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")
                })
            return results
        else:
            logger.warning(f"Tavily API returned status {res.status_code}: {res.text}")
            return []

async def search_duckduckgo_fallback(query: str) -> List[Dict[str, str]]:
    """Fallback search using DuckDuckGo HTML scraping if Tavily is unavailable."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            res = await client.post(url, data={"q": query}, headers=headers)
            if res.status_code == 200:
                html = res.text
                results = []
                from urllib.parse import unquote
                
                blocks = re.findall(r'<div[^>]*class="[^"]*results_links[^"]*"[^>]*>(.*?)(?=<div[^>]*class="[^"]*results_links[^"]*"|</body>)', html, re.DOTALL)
                
                for block in blocks:
                    if "result--ad" in block:
                        continue
                    
                    title_match = re.search(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
                    if not title_match:
                        continue
                    
                    raw_url = title_match.group(1)
                    actual_url = raw_url
                    if "uddg=" in raw_url:
                        url_m = re.search(r'uddg=(https?[^&"]+)', raw_url)
                        if url_m:
                            actual_url = unquote(url_m.group(1))
                    
                    clean_title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                    clean_title = unquote(clean_title).replace('&amp;', '&').replace('&#x27;', "'")
                    
                    snippet_match = re.search(r'class="result__snippet[^"]*"[^>]*>(.*?)</a>', block, re.DOTALL)
                    snippet = ""
                    if snippet_match:
                        snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                        snippet = unquote(snippet).replace('&amp;', '&').replace('&#x27;', "'")
                    
                    if clean_title and actual_url and not actual_url.startswith("/"):
                        results.append({
                            "title": clean_title,
                            "url": str(actual_url),
                            "snippet": snippet
                        })
                return results[:5]
    except Exception as e:
        logger.error(f"DuckDuckGo fallback search failed: {e}")
    return []


def extract_clean_search_query(raw_query: str) -> str:
    """Extracts concise search terms if full refusal message text is passed as raw_query."""
    if not raw_query:
        return raw_query
    # Check for regarding "topic"
    match = re.search(r'regarding\s*["\']?([^"\'.\n]+)["\']?', raw_query, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    clean = re.sub(r'This isn\'t covered in the document.*', '', raw_query, flags=re.IGNORECASE | re.DOTALL).strip()
    clean = re.sub(r'The uploaded document\(s\) do not contain information.*', '', clean, flags=re.IGNORECASE | re.DOTALL).strip()
    return clean if clean else raw_query

async def execute_web_search_and_synthesize(query: str) -> Dict[str, Any]:
    """
    Executes external web search, logs query audit, and synthesizes cited web response via LLM.
    """
    clean_query = extract_clean_search_query(query)
    
    # Audit log every web search query
    timestamp = datetime.utcnow().isoformat()
    logger.info(f"[WebSearch Audit Log] [{timestamp}] Executing external web search for query: '{clean_query}' (raw: '{query}')")

    results: List[Dict[str, str]] = []
    provider_used = "None"

    # Attempt Tavily API if configured
    if settings.TAVILY_API_KEY and settings.TAVILY_API_KEY.strip():
        try:
            results = await search_tavily(clean_query, settings.TAVILY_API_KEY.strip())
            if results:
                provider_used = "Tavily API"
        except Exception as e:
            logger.error(f"Tavily search error: {e}")

    # Fall back to DuckDuckGo if Tavily yielded no results
    if not results:
        results = await search_duckduckgo_fallback(clean_query)
        if results:
            provider_used = "DuckDuckGo HTML Fallback"


    if not results:
        logger.warning(f"[WebSearch Audit Log] No search results returned for query: '{query}'")
        return {
            "answer": "Web search didn't return results for this.",
            "web_citations": []
        }

    logger.info(f"[WebSearch Audit Log] Found {len(results)} results via {provider_used}")

    # Build web search context string for LLM
    context_str = f"WEB SEARCH RESULTS FOR QUERY: '{query}'\n\n"
    for idx, r in enumerate(results, 1):
        context_str += f"RESULT {idx}:\n"
        context_str += f"Title: {r['title']}\n"
        context_str += f"URL: {r['url']}\n"
        context_str += f"Snippet: {r['snippet']}\n\n"

    system_prompt = """You are SmartDoc Web Search Synthesis Assistant. Synthesize a clear, accurate, and concise answer to the user's question based EXCLUSIVELY on the provided web search results.

CRITICAL MANDATORY RULES:
1. CITATIONS: Every claim or fact MUST be cited with a clickable markdown link using the source URL: [Source Title](URL).
2. DO NOT hallucinate facts, dates, or URLs not present in the provided search results.
3. Use clean Markdown headers (### Header) and bullet points (- Point).
4. Clearly state that this information is retrieved from live web search.
"""

    # Call LLM provider with search context using dedicated web search synthesis
    provider = get_llm_provider()
    answer = await provider.synthesize_web_search(clean_query, results)

    # Fallback formatting directly from web search snippets if empty
    if not answer or "didn't return results" in answer.lower() or "do not contain information" in answer.lower():
        answer = f"### Web Search Results for '{clean_query}'\n\n"
        for r in results:
            answer += f"- **[{r['title']}]({r['url']})**: {r['snippet']}\n"

    return {
        "answer": answer,
        "web_citations": [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"]
            }
            for r in results
        ]
    }
