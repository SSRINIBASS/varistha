"""Web search execution supporting public search engines and deterministic mock mode."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

DEFAULT_USER_AGENT = "VaristhaBot/0.1 (+https://varistha.ai)"
DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"


def _clean_text(raw: str) -> str:
    """Strip HTML tags, unescape HTML entities, and normalize whitespace."""
    stripped = re.sub(r"<[^>]+>", " ", raw)
    unescaped = html.unescape(stripped)
    return " ".join(unescaped.split())


def _extract_duckduckgo_url(raw_href: str) -> str:
    """Extract real destination URL from DuckDuckGo redirect link."""
    if "duckduckgo.com/l/?" in raw_href:
        parsed = urlparse(raw_href)
        query_params = parse_qs(parsed.query)
        if query_params.get("uddg"):
            return unquote(query_params["uddg"][0])
        return raw_href


def parse_duckduckgo_html(html_content: str, max_results: int = 5) -> list[dict[str, str]]:
    """Parse DuckDuckGo HTML search results page."""
    results: list[dict[str, str]] = []

    # Match each result block
    result_blocks = re.findall(
        r'<div[^>]*class="[^"]*result\s+results_links[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html_content,
        re.DOTALL | re.IGNORECASE,
    )

    if not result_blocks:
        # Fallback simpler regex for results
        result_blocks = re.findall(
            r'<div[^>]*class="[^"]*result__body[^"]*"[^>]*>(.*?)</div>',
            html_content,
            re.DOTALL | re.IGNORECASE,
        )

    for block in result_blocks:
        # Extract title and link
        title_match = re.search(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if not title_match:
            continue

        raw_url = title_match.group(1).strip()
        raw_title = title_match.group(2).strip()

        dest_url = _extract_duckduckgo_url(raw_url)
        clean_title = _clean_text(raw_title)

        # Extract snippet
        snippet_match = re.search(
            r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if not snippet_match:
            snippet_match = re.search(
                r'<div[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>',
                block,
                re.DOTALL | re.IGNORECASE,
            )

        clean_snippet = _clean_text(snippet_match.group(1)) if snippet_match else ""

        if dest_url and clean_title:
            results.append({
                "title": clean_title,
                "url": dest_url,
                "snippet": clean_snippet,
            })

        if len(results) >= max_results:
            break

    return results


async def search_web(
    query: str,
    max_results: int = 5,
    engine: str = "duckduckgo",
    timeout_seconds: float = 10.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any]:
    """Execute a public web search query and return structured citations.

    Args:
        query: Search term or question.
        max_results: Max results to return (default 5).
        engine: Search provider ('duckduckgo' or 'mock').
        timeout_seconds: Request timeout in seconds.
        user_agent: User-Agent header string.

    Returns:
        Structured dictionary with query, engine, results list, and total count.

    """
    clean_query = query.strip()
    if not clean_query:
        return {
            "query": query,
            "engine": engine,
            "results": [],
            "total_results": 0,
        }

    # Deterministic mock search for offline and test runs
    if engine == "mock":
        mock_results = [
            {
                "title": f"Result 1 for {clean_query}",
                "url": "https://example.com/item-1",
                "snippet": f"Overview and facts concerning {clean_query}.",
            },
            {
                "title": f"Result 2 for {clean_query}",
                "url": "https://example.com/item-2",
                "snippet": f"Detailed analysis and documentation for {clean_query}.",
            },
            {
                "title": f"Result 3 for {clean_query}",
                "url": "https://example.com/item-3",
                "snippet": f"Market intelligence report and insights regarding {clean_query}.",
            },
        ]
        slice_results = mock_results[:max_results]
        return {
            "query": clean_query,
            "engine": "mock",
            "results": slice_results,
            "total_results": len(slice_results),
        }

    # Live DuckDuckGo HTML Search
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    data = {"q": clean_query, "b": ""}

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            response = await client.post(DUCKDUCKGO_HTML_URL, data=data, headers=headers)
            response.raise_for_status()
            results = parse_duckduckgo_html(response.text, max_results=max_results)
    except Exception:
        # On connection error, timeout, or rate-limiting, return empty results gracefully
        results = []

    return {
        "query": clean_query,
        "engine": engine,
        "results": results,
        "total_results": len(results),
    }
