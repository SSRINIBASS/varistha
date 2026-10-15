"""Web page fetcher with HTML-to-text extraction and SSRF validation."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import httpx
from ssrf import SSRFSecurityError, validate_url_against_ssrf

DEFAULT_USER_AGENT = "VaristhaBot/0.1 (+https://varistha.ai)"


def extract_title_and_text(html: str) -> tuple[str, str]:
    """Extract page title and clean text from raw HTML content."""
    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""

    # Remove script, style, and title elements from body text
    cleaned = re.sub(
        r"<(script|style|svg|noscript|title)[^>]*>.*?</\1>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove all other HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Normalize whitespace
    text = " ".join(cleaned.split())
    return title, text


async def fetch_url(
    url: str,
    max_chars: int = 10000,
    timeout_seconds: float = 10.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any]:
    """Safely fetch a web page over HTTP/HTTPS with SSRF defense.

    Args:
        url: The web URL to fetch.
        max_chars: Maximum characters of extracted text to return.
        timeout_seconds: Request timeout in seconds.
        user_agent: Custom User-Agent header string.

    Returns:
        Structured dictionary containing extracted text and untrusted metadata.

    Raises:
        SSRFSecurityError: If any target URL or redirect URL violates SSRF safety rules.
        httpx.HTTPError: If the HTTP request fails.

    """
    validate_url_against_ssrf(url)

    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,text/plain"}

    current_url = url
    max_redirects = 5
    redirect_count = 0

    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=False,
    ) as client:
        while True:
            response = await client.get(current_url, headers=headers)

            if response.is_redirect and "location" in response.headers:
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise SSRFSecurityError(f"Too many redirects ({redirect_count}).")

                next_url = urljoin(current_url, response.headers["location"])
                validate_url_against_ssrf(next_url)
                current_url = next_url
                continue

            break

    content_type = response.headers.get("content-type", "")
    raw_content = response.text

    if "text/html" in content_type:
        title, text = extract_title_and_text(raw_content)
    else:
        title = ""
        text = " ".join(raw_content.split())

    truncated_content = text[:max_chars]

    return {
        "url": url,
        "final_url": current_url,
        "status_code": response.status_code,
        "title": title,
        "content": truncated_content,
        "untrusted": True,
    }
