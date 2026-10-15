"""Web fetch plugin for Varistha."""

from __future__ import annotations

from fetcher import fetch_url
from ssrf import SSRFSecurityError, validate_url_against_ssrf

__all__ = [
    "SSRFSecurityError",
    "fetch_url",
    "validate_url_against_ssrf",
]
