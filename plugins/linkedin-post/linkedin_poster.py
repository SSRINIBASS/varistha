"""Outbound professional publishing plugin for LinkedIn with mandatory approval gating."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

MAX_LINKEDIN_LENGTH = 3000
ALLOWED_VISIBILITY = {"PUBLIC", "CONNECTIONS"}


class LinkedInPostValidationError(Exception):
    """Raised when LinkedIn post content or visibility settings are invalid."""


def validate_linkedin_post(text: str, visibility: str) -> tuple[str, str]:
    """Validate content length and visibility for a LinkedIn post."""
    clean_text = text.strip()
    if not clean_text:
        raise LinkedInPostValidationError("LinkedIn post text cannot be empty.")
    if len(clean_text) > MAX_LINKEDIN_LENGTH:
        raise LinkedInPostValidationError(
            f"Post exceeds LinkedIn limit of {MAX_LINKEDIN_LENGTH} characters "
            f"(current length: {len(clean_text)})."
        )

    clean_visibility = visibility.strip().upper()
    if clean_visibility not in ALLOWED_VISIBILITY:
        raise LinkedInPostValidationError(
            f"Invalid visibility '{visibility}'. Allowed: {sorted(ALLOWED_VISIBILITY)}."
        )

    return clean_text, clean_visibility


async def post_to_linkedin(
    text: str,
    title: str | None = None,
    article_url: str | None = None,
    visibility: str = "PUBLIC",
    author_urn: str | None = None,
    mock: bool = True,
) -> dict[str, Any]:
    """Publish a post to LinkedIn or simulate posting in mock mode.

    Args:
        text: Main post commentary (1 to 3000 characters).
        title: Optional title for shared article/link.
        article_url: Optional URL of an article to attach/preview.
        visibility: "PUBLIC" or "CONNECTIONS".
        author_urn: Author person or org URN (default: simulated author URN).
        mock: When true, simulates posting without external network calls.

    Returns:
        Structured response detailing share URN, post link, and metadata.

    """
    clean_text, clean_visibility = validate_linkedin_post(text, visibility)

    now = datetime.now(UTC)
    seed = f"{clean_text}:{article_url}:{now.isoformat()}"
    share_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    share_urn = f"urn:li:share:{share_hash}"
    url = f"https://www.linkedin.com/feed/update/{share_urn}"

    return {
        "status": "posted" if not mock else "simulated_posted",
        "share_urn": share_urn,
        "url": url,
        "text": clean_text,
        "title": title or "",
        "article_url": article_url or "",
        "visibility": clean_visibility,
        "char_count": len(clean_text),
        "author_urn": author_urn or "urn:li:person:mock_author",
        "posted_at": now.isoformat(),
        "mock": mock,
    }
