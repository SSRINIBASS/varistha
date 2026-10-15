"""Web scrape plugin for Varistha."""

from __future__ import annotations

from scraper import (
    convert_html_to_markdown,
    extract_headings_from_html,
    extract_links_from_html,
    extract_metadata,
    scrape_url,
)
from ssrf import SSRFSecurityError, validate_url_against_ssrf

__all__ = [
    "SSRFSecurityError",
    "convert_html_to_markdown",
    "extract_headings_from_html",
    "extract_links_from_html",
    "extract_metadata",
    "scrape_url",
    "validate_url_against_ssrf",
]
