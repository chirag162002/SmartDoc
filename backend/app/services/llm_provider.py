import json
import re
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.llm.claude_client import claude_client
from app.services.llm_validation import (
    validate_citation_tags,
    fact_check_numeric_claims,
    verify_and_filter_key_numbers,
    verify_qualitative_claims,
    sanitize_analysis_output,
    extract_and_parse_json,
    generate_extractive_fallback
)

class LLMProvider(ABC):
    @abstractmethod
    async def summarize(
        self,
        chunks: List[Dict[str, Any]],
        filename: str,
        is_tabular: bool = False,
        tabular_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Summarizes and analyzes document chunks into structured JSON."""
        pass

    @abstractmethod
    async def chat(
        self,
        user_query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Answers grounded follow-up chat queries using context chunks."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Checks if the LLM provider service is reachable and functional."""
        pass

    @abstractmethod
    async def synthesize_web_search(
        self,
        query: str,
        web_results: List[Dict[str, str]]
    ) -> str:
        """Synthesizes live external web search results into a clean, accurate cited response."""
        pass


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE

    async def check_ollama_health(self) -> Tuple[bool, Optional[str]]:
        """
        Checks Ollama connectivity and model presence.
        Returns (is_healthy, specific_error_message).
        """
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code != 200:
                    return False, f"Cannot connect to Ollama at {self.base_url}. Is 'ollama serve' running?"
                
                data = res.json()
                models_installed = [m.get("name", "") for m in data.get("models", [])]
                
                model_match = any(
                    self.model == m or 
                    self.model in m or 
                    m.startswith(self.model) or
                    m.split(':')[0] == self.model.split(':')[0]
                    for m in models_installed
                )
                
                if not model_match:
                    return False, f"Model '{self.model}' not found locally. Run 'ollama pull {self.model}'."
                    
                return True, None
        except (httpx.ConnectError, httpx.ConnectTimeout):
            return False, f"Cannot connect to Ollama at {self.base_url}. Is 'ollama serve' running?"
        except Exception as e:
            return False, f"Cannot connect to Ollama at {self.base_url}: {str(e)}"

    async def health_check(self) -> bool:
        is_healthy, _ = await self.check_ollama_health()
        return is_healthy

    async def summarize(
        self,
        chunks: List[Dict[str, Any]],
        filename: str,
        is_tabular: bool = False,
        tabular_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        is_healthy, error_detail = await self.check_ollama_health()
        if not is_healthy:
            logger.error(f"[OllamaProvider Error]: {error_detail}")
            return generate_extractive_fallback(chunks, filename, error_notice=error_detail)

        valid_chunk_ids = [c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}") for c in chunks]
        
        context_text = f"DOCUMENT FILENAME: {filename}\n\nCHUNKS:\n"
        for c in chunks:
            cid = c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}")
            page = c.get("page_number", 1)
            context_text += f"--- [{cid}] (Page {page}) ---\n{c.get('content', '')}\n"

        if is_tabular or any("=== Spreadsheet Sheet:" in c.get("content", "") for c in chunks):
            system_prompt = """You are SmartDoc Tabular Data & Financial Spreadsheet Intelligence Analyzer. Analyze the provided spreadsheet dataset chunks (CSV/Excel) and extract executive business insights.

CRITICAL TABULAR INSTRUCTIONS:
1. "executive_summary": Write a brief, highly structured business summary of this dataset:
   - **Dataset Type & Scope**: Describe the dataset domain (e.g. GST E-Commerce Sales & Tax Register, Financial Ledger, Inventory Tracker). State total row and column dimensions. Include citation [Ref: CHUNK-...].
   - **Financial & Operational Highlights**: State key financial totals (e.g. Total Revenue / Invoice Amount sum, Total Tax Amount, Total Transaction Volume, Date Range).
   - **Key Findings & Observations**: Summarize primary transaction types, top geographic regions (states/cities), or primary fulfillment categories.
   - **Data Insights**: Highlight key business patterns or tax compliance notes.

2. "detailed_summary": Write a section-by-section breakdown using Markdown headers (### Section Title) covering:
   - ### Dataset Overview & Schema
   - ### Financial & Quantitative Totals
   - ### Regional & Categorical Breakdown

3. "entities": Extract actual named entities (seller GSTINs, locations/states, fulfillment channels, primary companies).
4. "topics": Extract 3 to 6 actual subject topics (e.g. GST Tax Register, E-Commerce Sales, Tax Accounting, Logistics).
5. "key_numbers_dates": Extract actual total sums, transaction counts, tax totals, or dates from the text.

Return ONLY valid JSON matching this schema:
{
  "executive_summary": "- **Dataset Type & Scope**: ... [Ref: CHUNK-...]\n- **Financial & Operational Highlights**: ... [Ref: CHUNK-...]\n- **Key Findings**: ... [Ref: CHUNK-...]",
  "detailed_summary": "### Section Title\\n- Detail... [Ref: CHUNK...]",
  "entities": [],
  "topics": [],
  "sentiment_tone": {"overall": "Objective Data Analysis", "confidence": 0.95},
  "key_numbers_dates": [],
  "risk_flags": [],
  "action_items": []
}
"""
        else:
            system_prompt = """You are SmartDoc Universal Document Intelligence Analyzer. Analyze the provided document chunks regardless of subject matter or file format.

CRITICAL DYNAMIC ADAPTATION INSTRUCTIONS:
1. DYNAMIC CLASSIFICATION & ADAPTIVE SUMMARY:
   Automatically determine the document type (e.g., Exam/Study Roadmap, Financial Statement, Legal Contract, Technical Manual, Resume/CV, Research Paper, Business Report, Dataset).
   Write a brief, highly structured "executive_summary" using bullet points (- **Heading**: details) relevant to THIS SPECIFIC document type:
   - For Roadmaps / Schedules / Plans: Summarize Goal/Objective, Timeline/Phases, Core Topics Covered, Milestones, and Execution Strategy.
   - For Financials / Reports: Summarize Primary Objective, Financial Metrics, Performance Highlights, and Strategic Insights.
   - For Contracts / Legal: Summarize Parties Involved, Key Obligations, Terms & Scope, and Critical Deadlines.
   - For Technical / Research: Summarize Main Innovation/Topic, Methodology, Key System Features, and Conclusions.
   - For Resumes / Profiles: Summarize Profile/Specialization, Work Experience, Key Projects, Education, and Skills.
   DO NOT output irrelevant headers like "No work experience mentioned" or "No education marks mentioned" for non-resume documents! Include source citations like [Ref: CHUNK-id-Page-N].

2. "detailed_summary": Write a complete section-by-section breakdown using Markdown headers (### Section Title) matching the document's actual chapters/sections and bullet points (- detail) with citations.
3. "entities": Extract actual named entities (key people, organizations, frameworks, modules, dates, locations) mentioned in the document.
4. "topics": Extract 3 to 6 actual subject topics discussed in the document.
5. "key_numbers_dates": Extract actual numbers, timelines, percentages, or dates present in the text (e.g. "14 Weeks", "CAT 2026", "77.28%"). Do NOT invent any numbers.

Return ONLY valid JSON matching this schema:
{
  "executive_summary": "- **Document Goal & Type**: ... [Ref: CHUNK-...]\n- **Core Overview**: ... [Ref: CHUNK-...]\n- **Key Highlights & Timeline**: ... [Ref: CHUNK-...]\n- **Actionable Takeaways**: ... [Ref: CHUNK-...]",
  "detailed_summary": "### Section Title\\n- Detail... [Ref: CHUNK...]",
  "entities": [],
  "topics": [],
  "sentiment_tone": {"overall": "Objective", "confidence": 0.9},
  "key_numbers_dates": [],
  "risk_flags": [],
  "action_items": []
}
"""
        prompt = f"Analyze the following document:\n{context_text}"

        response_json, call_err = await self._call_ollama(prompt, system_prompt, temperature=self.temperature, enforce_json=True)
        if call_err:
            logger.warning(f"[Ollama Call Error]: {call_err}. Falling back to extractive summary.")
            return generate_extractive_fallback(chunks, filename, error_notice=call_err)
        
        is_valid_cit, invalid_tags = validate_citation_tags(response_json, valid_chunk_ids)
        if not is_valid_cit:
            logger.warning(f"[Ollama Citation Validation Retry]: Invalid tags {invalid_tags}. Retrying...")
            retry_prompt = f"{prompt}\n\nWARNING: Previous output used invalid chunk IDs {invalid_tags}. Use ONLY: {valid_chunk_ids}."
            response_json, call_err = await self._call_ollama(retry_prompt, system_prompt, temperature=self.temperature, enforce_json=True)
            if call_err:
                return generate_extractive_fallback(chunks, filename, error_notice=call_err)

        # Sanitize prompt template echoes (e.g. "Comprehensive 360-degree...", dummy topics/entities)
        response_json = sanitize_analysis_output(response_json, chunks, filename)

        # Fact check and filter key numbers/dates against source text to eliminate hallucinated prompt numbers
        full_chunks_text = "\n".join([c.get("content", "") for c in chunks])
        if "key_numbers_dates" in response_json and isinstance(response_json["key_numbers_dates"], list):
            response_json["key_numbers_dates"] = verify_and_filter_key_numbers(
                response_json["key_numbers_dates"], full_chunks_text
            )

        # Fact check and filter qualitative entity and topic claims against source text
        v_entities, v_topics = verify_qualitative_claims(
            response_json.get("entities", []),
            response_json.get("topics", []),
            full_chunks_text
        )
        if v_entities:
            response_json["entities"] = v_entities
        if v_topics:
            response_json["topics"] = v_topics

        return response_json

    async def chat(
        self,
        user_query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        is_healthy, error_detail = await self.check_ollama_health()
        if not is_healthy:
            return {
                "answer": f"Ollama Error: {error_detail}",
                "citations": []
            }

        context_text = "SOURCE CHUNKS:\n"
        citations_lookup = []
        
        for c in context_chunks:
            cid = c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}")
            page = c.get("page_number", 1)
            context_text += f"--- [{cid}] (Page {page}) ---\n{c.get('content', '')}\n"
            citations_lookup.append({
                "doc_id": c.get("doc_id", "doc"),
                "chunk_id": cid,
                "page_number": page,
                "snippet": c.get("content", "")[:150] + "..."
            })

        system_prompt = """You are SmartDoc Grounded Chat Assistant. Answer the user question EXCLUSIVELY using the source chunks provided.

CRITICAL DIRECT REFUSAL RULE (HIGHEST PRIORITY):
If the user's question asks for opinion, quality evaluation, reviews, rankings, external facts, or any information NOT directly stated in the source chunks (e.g. "is X a good college?", "is this company reputable?", "what is the stock price?"), DO NOT generate meta-narrative essays, headers, or speculative chatter.
INSTEAD, RESPOND IMMEDIATELY AND ONLY WITH THIS EXACT SENTENCE:
"The uploaded document(s) do not contain information regarding this topic."

STRICT QUERY SCOPING & CATEGORIZATION ACCURACY RULES:
1. STRICT CATEGORY ACCURACY: Answer ONLY what the user specifically asked for based on the document's actual content.
   - Do NOT mix up or lump distinct categories together under inaccurate labels!
   - Specific Education Rule: If the user asks for "college marks" or "university grades", return ONLY degree/college marks (e.g. BCA, B.Tech, Master's, CGPA). Do NOT include 10th Grade or 12th Grade school marks under "college marks"!
   - Specific Work Rule: If asked for "work experience", do NOT include personal projects or high school unless requested.
   - Specific Skills Rule: If asked for "skills", do NOT include job titles.
2. NO META-CHATTER: State the facts directly. Never output meta-phrases like "The user inquired about...", "According to the provided source chunk...", or "In conclusion...".
3. Format your response in clean Markdown with bullet points (- item). Use double newlines between sections.
4. Put every item on its OWN line.
5. NEVER output raw ASCII horizontal rules like '=====' or '-----'.
6. Every single claim MUST include a citation tag [Ref: CHUNK-id-Page-N] referencing the exact source chunk.
7. NEVER append manual redundant text like "(Page 1)" or "(Page N)" after citation tags. Output ONLY [Ref: CHUNK-id-Page-N].
"""
        prompt = f"{context_text}\nUSER QUESTION:\n{user_query}"

        res, call_err = await self._call_ollama(prompt, system_prompt, temperature=0.1, enforce_json=False)
        if call_err:
            return {"answer": f"Ollama Error: {call_err}", "citations": []}
            
        answer = res.get("answer") or res.get("executive_summary") or res.get("detailed_summary", "Answer generated from source chunks.")

        return {
            "answer": answer,
            "citations": citations_lookup[:5]
        }

    async def synthesize_web_search(
        self,
        query: str,
        web_results: List[Dict[str, str]]
    ) -> str:
        context_str = f"USER QUESTION: '{query}'\n\nLIVE EXTERNAL WEB SEARCH RESULTS:\n"
        for idx, r in enumerate(web_results, 1):
            context_str += f"--- [Result {idx}] ---\n"
            context_str += f"Title: {r['title']}\n"
            context_str += f"URL: {r['url']}\n"
            context_str += f"Snippet: {r['snippet']}\n\n"

        system_prompt = """You are SmartDoc Live Web Search Synthesis Assistant. Synthesize a comprehensive, helpful, and accurate response to the user's question based EXCLUSIVELY on the provided web search results.

CRITICAL INSTRUCTIONS:
1. DIRECT HELPFUL ANSWER FIRST: Provide a direct, detailed evaluation/answer to the user's question upfront (e.g. key facts, rankings, NIRF/NAAC accreditation, courses, fees, reputation, pros/cons, overall quality).
2. CITATIONS: Include markdown links to source URLs [Source Title](URL) for key facts.
3. FORMATTING: Use clean Markdown headers (### Header) and bullet points (- item). Use double newlines between sections.
4. DO NOT say "The uploaded document does not contain information". This is LIVE WEB SEARCH synthesis, NOT document search!
"""
        res, call_err = await self._call_ollama(context_str, system_prompt, temperature=0.2, enforce_json=False)
        if call_err or not res.get("answer"):
            out = f"### Web Search Synthesis for '{query}'\n\n"
            for r in web_results:
                out += f"- **[{r['title']}]({r['url']})**: {r['snippet']}\n"
            return out
        
        return res.get("answer", "")

    async def _call_ollama(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        enforce_json: bool = False
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "options": {
                "temperature": temperature,
                "num_predict": 1536,
                "num_ctx": 4096
            },
            "stream": False
        }
        
        if enforce_json:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 404:
                    return {}, f"Model '{self.model}' not found locally. Run 'ollama pull {self.model}'."
                elif res.status_code != 200:
                    return {}, f"Ollama server returned HTTP {res.status_code}: {res.text}"
                    
                data = res.json()
                content = data.get("message", {}).get("content", "").strip()
                
                if not content:
                    return {}, "Ollama returned empty response content."

                if enforce_json:
                    parsed_json, parse_err = extract_and_parse_json(content)
                    if parsed_json and isinstance(parsed_json, dict):
                        return parsed_json, None
                    else:
                        logger.error(f"[Ollama JSON Parse Error]: {parse_err}")
                        return {}, f"Could not parse valid JSON from LLM output: {parse_err}"

                clean_answer = content.replace('\\n', '\n')
                return {
                    "answer": clean_answer,
                    "executive_summary": clean_answer,
                    "detailed_summary": clean_answer,
                    "entities": [],
                    "topics": [],
                    "sentiment_tone": {"overall": "Objective", "confidence": 1.0},
                    "key_numbers_dates": [],
                    "risk_flags": [],
                    "action_items": []
                }, None

        except (httpx.ConnectError, httpx.ConnectTimeout):
            return {}, f"Cannot connect to Ollama at {self.base_url}. Is 'ollama serve' running?"
        except httpx.ReadTimeout:
            return {}, "Ollama request timed out after 120s — the model may be too large for available hardware."
        except Exception as e:
            return {}, f"Ollama API request failed: {str(e)}"


class ClaudeProvider(LLMProvider):
    async def health_check(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    async def summarize(
        self,
        chunks: List[Dict[str, Any]],
        filename: str,
        is_tabular: bool = False,
        tabular_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        from app.services.map_reduce import process_map_reduce_analysis
        return await process_map_reduce_analysis(
            doc_id="claude_doc",
            filename=filename,
            chunks=chunks,
            is_tabular=is_tabular,
            tabular_stats=tabular_stats
        )

    async def chat(
        self,
        user_query: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        context_text = ""
        citations_lookup = []
        for c in context_chunks:
            cid = c.get("chunk_id", f"CHUNK-{c.get('chunk_index', 0)}")
            page = c.get("page_number", 1)
            context_text += f"\n--- [{cid}] (Page {page}) ---\n{c.get('content', '')}\n"
            citations_lookup.append({
                "doc_id": c.get("doc_id", "doc"),
                "chunk_id": cid,
                "page_number": page,
                "snippet": c.get("content", "")[:150] + "..."
            })
            
        system_prompt = """You are SmartDoc Claude Assistant. Answer using ONLY provided chunks.
STRICT QUERY RELEVANCE: Answer ONLY what the user asked for (e.g. if asked for Work Experience, return ONLY employment roles; do NOT include projects or education). Format responses in clean, structured Markdown with double newlines between sections, numbered roles/items, bullet lists, and [Ref: CHUNK-...] citations."""
        prompt = f"CHUNKS:\n{context_text}\nUSER QUERY:\n{user_query}"
        
        res = await claude_client.generate_json_response(prompt=prompt, system_prompt=system_prompt, temperature=0.2)
        answer = res.get("executive_summary") or res.get("answer") or "Claude answer generated."
        
        return {"answer": answer, "citations": citations_lookup[:5]}

    async def synthesize_web_search(
        self,
        query: str,
        web_results: List[Dict[str, str]]
    ) -> str:
        context_str = f"USER QUESTION: '{query}'\n\nLIVE EXTERNAL WEB SEARCH RESULTS:\n"
        for idx, r in enumerate(web_results, 1):
            context_str += f"--- [Result {idx}] ---\n"
            context_str += f"Title: {r['title']}\n"
            context_str += f"URL: {r['url']}\n"
            context_str += f"Snippet: {r['snippet']}\n\n"

        system_prompt = """You are SmartDoc Live Web Search Synthesis Assistant. Synthesize a clear, accurate, and concise answer to the user's question based EXCLUSIVELY on the provided web search results. Include source URL markdown links [Title](URL)."""
        res = await claude_client.generate_json_response(prompt=context_str, system_prompt=system_prompt, temperature=0.2)
        return res.get("answer") or res.get("executive_summary") or f"Web search synthesis complete for '{query}'."


def get_llm_provider() -> LLMProvider:
    """Factory function returning configured LLMProvider instance."""
    provider_type = settings.LLM_PROVIDER.lower()
    if provider_type == "ollama":
        return OllamaProvider()
    else:
        return ClaudeProvider()
