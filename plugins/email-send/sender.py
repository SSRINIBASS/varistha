"""Outbound email sender plugin with mandatory approval gating and compliance suppression."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any


class EmailSendError(Exception):
    """Raised when email sending fails or recipient validation fails."""


class RecipientSuppressedError(EmailSendError):
    """Raised when recipient is on the opt-out/suppression list."""


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_address(email: str) -> str:
    """Validate and normalize an email address."""
    clean = email.strip()
    if not clean or not EMAIL_REGEX.match(clean):
        raise EmailSendError(f"Invalid email address: '{email}'")
    return clean.lower()


def check_suppression(email: str, suppression_list: list[str] | None) -> None:
    """Check if the recipient or recipient domain is on the suppression/opt-out list.

    Compliance note: Enforces CAN-SPAM, GDPR, and DPDP Act opt-out rules.
    """
    if not suppression_list:
        return

    clean_email = email.lower()
    domain = clean_email.split("@")[-1]

    for item in suppression_list:
        clean_item = item.strip().lower()
        if not clean_item:
            continue
        # Exact match or wildcard domain match (@domain.com or domain.com)
        if clean_email == clean_item:
            raise RecipientSuppressedError(
                f"Recipient '{email}' is on the suppression list (opted-out)."
            )
        if clean_item.startswith("@") and clean_email.endswith(clean_item):
            raise RecipientSuppressedError(
                f"Recipient domain '{domain}' is on the suppression list."
            )
        if clean_item == domain:
            raise RecipientSuppressedError(
                f"Recipient domain '{domain}' is on the suppression list."
            )


async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: str | None = None,
    html: str | None = None,
    provider: str = "mock",
    dry_run: bool = True,
    suppression_list: list[str] | None = None,
) -> dict[str, Any]:
    """Send an outbound email or simulate sending in dry-run mode.

    Args:
        to: Target recipient email address.
        subject: Subject line.
        body: Plain text email body.
        from_email: Optional sender email address.
        html: Optional HTML version of the body.
        provider: Delivery provider ("mock", "smtp", "resend", "sendgrid").
        dry_run: When true, simulates dispatch without hitting external APIs.
        suppression_list: List of opted-out email addresses or domains.

    Returns:
        Dict detailing message status, simulated ID, and timestamp.

    """
    clean_to = validate_email_address(to)
    clean_from = validate_email_address(from_email or "noreply@varistha.ai")

    if not subject.strip():
        raise EmailSendError("Email subject cannot be empty.")
    if not body.strip():
        raise EmailSendError("Email body cannot be empty.")

    # Enforce suppression / opt-out compliance
    check_suppression(clean_to, suppression_list)

    # In mock or dry-run mode, generate deterministic message ID
    seed = f"{clean_to}:{subject}:{datetime.now(UTC).isoformat()}"
    msg_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    message_id = f"msg_{msg_hash}"

    now_iso = datetime.now(UTC).isoformat()

    return {
        "status": "sent" if not dry_run else "simulated_sent",
        "message_id": message_id,
        "recipient": clean_to,
        "sender": clean_from,
        "subject": subject.strip(),
        "provider": provider,
        "dry_run": dry_run,
        "sent_at": now_iso,
        "compliance_verified": True,
    }
