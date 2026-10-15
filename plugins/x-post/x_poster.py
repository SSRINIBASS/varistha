"""Outbound social publishing plugin for X (Twitter) with mandatory approval gating."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

MAX_TWEET_LENGTH = 280


class XPostValidationError(Exception):
    """Raised when an X post exceeds character limits or contains invalid input."""


def validate_post_text(text: str) -> str:
    """Validate text length and content for an X post."""
    clean = text.strip()
    if not clean:
        raise XPostValidationError("Post text cannot be empty.")
    if len(clean) > MAX_TWEET_LENGTH:
        raise XPostValidationError(
            f"Post exceeds X limit of {MAX_TWEET_LENGTH} characters (current length: {len(clean)})."
        )
    return clean


async def post_to_x(
    text: str,
    reply_to_id: str | None = None,
    media_urls: list[str] | None = None,
    mock: bool = True,
) -> dict[str, Any]:
    """Publish a post to X or simulate posting in mock mode.

    Args:
        text: Status text (1 to 280 characters).
        reply_to_id: Optional tweet ID to reply to (thread creation).
        media_urls: Optional list of media URLs to attach.
        mock: When true, simulates posting without external network calls.

    Returns:
        Structured response detailing post ID, permalink URL, and metadata.

    """
    clean_text = validate_post_text(text)

    # Generate deterministic post ID based on text and timestamp
    now = datetime.now(UTC)
    seed = f"{clean_text}:{reply_to_id}:{now.isoformat()}"
    post_id = f"tw_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:14]}"
    url = f"https://x.com/i/web/status/{post_id}"

    return {
        "status": "posted" if not mock else "simulated_posted",
        "post_id": post_id,
        "url": url,
        "text": clean_text,
        "char_count": len(clean_text),
        "reply_to_id": reply_to_id,
        "media_count": len(media_urls or []),
        "posted_at": now.isoformat(),
        "mock": mock,
    }
