"""Deep webpage scraper and clean markdown extractor with SSRF protection."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from ssrf import SSRFSecurityError, validate_url_against_ssrf

DEFAULT_USER_AGENT = "VaristhaBot/0.1 (+https://varistha.ai)"


def extract_metadata(html_content: str) -> tuple[str, str]:
    """Extract page title and meta description from HTML."""
    # Title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    title = html.unescape(title_match.group(1).strip()) if title_match else ""

    # Meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\'](.*?)["\']',
            html_content,
            re.IGNORECASE | re.DOTALL,
        )

    meta_desc = html.unescape(desc_match.group(1).strip()) if desc_match else ""
    return title, meta_desc


def extract_headings_from_html(html_content: str) -> list[str]:
    """Extract h1, h2, h3 headings in reading order."""
    headings: list[str] = []
    matches = re.findall(
        r"<h[1-3][^>]*>(.*?)</h[1-3]>",
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    for raw in matches:
        clean = " ".join(html.unescape(re.sub(r"<[^>]+>", "", raw)).split())
        if clean:
            headings.append(clean)
    return headings


def extract_links_from_html(html_content: str, base_url: str) -> list[dict[str, str]]:
    """Extract outbound and contextual hyperlinks."""
    links: list[dict[str, str]] = []
    matches = re.findall(
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    seen_urls: set[str] = set()

    for href, text in matches:
        clean_href = href.strip()
        if not clean_href or clean_href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        clean_text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", text)).split())
        abs_url = urljoin(base_url, clean_href)

        if (
            abs_url.startswith(("http://", "https://"))
            and abs_url not in seen_urls
            and clean_text
        ):
            seen_urls.add(abs_url)
            links.append({"text": clean_text, "url": abs_url})

    return links


def convert_html_to_markdown(raw_html: str) -> str:
    """Convert raw HTML body into readable, clean markdown."""
    # Strip non-content blocks
    cleaned = re.sub(
        r"<(script|style|svg|noscript|header|footer|nav|aside|iframe)[^>]*>.*?</\1>",
        "",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert headings
    cleaned = re.sub(
        r"<h1[^>]*>(.*?)</h1>",
        lambda m: f"\n\n# {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"<h2[^>]*>(.*?)</h2>",
        lambda m: f"\n\n## {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"<h3[^>]*>(.*?)</h3>",
        lambda m: f"\n\n### {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert list items
    cleaned = re.sub(
        r"<li[^>]*>(.*?)</li>",
        lambda m: f"\n- {re.sub(r'<[^>]+>', '', m.group(1)).strip()}",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Convert paragraphs and breaks
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<p[^>]*>", "\n\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</p>", "\n\n", cleaned, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    unescaped = html.unescape(cleaned)

    # Normalize whitespace while preserving paragraphs
    lines: list[str] = []
    for line in unescaped.splitlines():
        trimmed = " ".join(line.split())
        if trimmed:
            lines.append(trimmed)
        elif lines and lines[-1] != "":
            lines.append("")

    return "\n".join(lines).strip()


async def scrape_url(
    url: str,
    max_chars: int = 25000,
    extract_headings: bool = True,
    extract_links: bool = True,
    timeout_seconds: float = 15.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict[str, Any]:
    """Scrape and extract structured markdown content with SSRF protection.

    Args:
        url: The web URL to scrape.
        max_chars: Maximum characters of markdown content.
        extract_headings: Whether to collect structured headings.
        extract_links: Whether to extract outbound hyperlinks.
        timeout_seconds: HTTP timeout in seconds.
        user_agent: Custom User-Agent header.

    Returns:
        Structured dictionary containing extracted text and untrusted metadata.

    Raises:
        SSRFSecurityError: If any target URL or redirect URL violates SSRF safety rules.
        httpx.HTTPError: If the HTTP request fails.

    """
    validate_url_against_ssrf(url)

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }

    current_url = url
    max_redirects = 5
    redirect_count = 0

    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
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

    raw_html = response.text
    title, meta_desc = extract_metadata(raw_html)
    headings = extract_headings_from_html(raw_html) if extract_headings else []
    links = extract_links_from_html(raw_html, current_url) if extract_links else []
    markdown = convert_html_to_markdown(raw_html)
    truncated_md = markdown[:max_chars]

    return {
        "url": url,
        "final_url": current_url,
        "status_code": response.status_code,
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "markdown": truncated_md,
        "links": links[:50],
        "char_count": len(truncated_md),
    }
