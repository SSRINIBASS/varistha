"""Contextual email composer plugin for drafting personalized communications."""

from __future__ import annotations

import re
from typing import Any


class EmailDraftError(Exception):
    """Raised when email drafting inputs are invalid."""


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_address(email: str) -> str:
    """Validate and normalize an email address."""
    clean = email.strip()
    if not clean or not EMAIL_REGEX.match(clean):
        raise EmailDraftError(f"Invalid email address: '{email}'")
    return clean.lower()


def interpolate_tokens(template: str, context: dict[str, Any]) -> str:
    """Replace {{token_name}} placeholders in template with context values."""
    result = template
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    return result


async def compose_email_draft(
    to: str,
    subject: str,
    body: str,
    recipient_name: str | None = None,
    context: dict[str, Any] | None = None,
    tone: str = "professional",
    sender_name: str | None = None,
    call_to_action: str | None = None,
) -> dict[str, Any]:
    """Compose a structured, tokenized email draft.

    Args:
        to: Target recipient email address.
        subject: Subject line (can contain {{tokens}}).
        body: Main body content (can contain {{tokens}}).
        recipient_name: Optional recipient name for greeting.
        context: Optional dictionary of variables for token replacement.
        tone: Writing tone ("professional", "friendly", "persuasive", "concise").
        sender_name: Optional sender name for signature.
        call_to_action: Optional explicit call to action text.

    Returns:
        Structured draft object containing subject, body, preview text, and metadata.

    """
    clean_to = validate_email_address(to)

    ctx: dict[str, Any] = dict(context or {})
    if recipient_name and "recipient_name" not in ctx:
        ctx["recipient_name"] = recipient_name
    if recipient_name and "first_name" not in ctx:
        ctx["first_name"] = recipient_name.split()[0]
    if sender_name and "sender_name" not in ctx:
        ctx["sender_name"] = sender_name
    if call_to_action and "call_to_action" not in ctx:
        ctx["call_to_action"] = call_to_action

    final_subject = interpolate_tokens(subject.strip(), ctx)
    final_body = interpolate_tokens(body.strip(), ctx)

    # Greeting if specified and not already in body
    if recipient_name and not final_body.lower().startswith(("hi ", "hello ", "dear ", "hey ")):
        greeting = f"Hi {ctx.get('first_name', recipient_name)},\n\n"
        final_body = greeting + final_body

    # Call to action if provided and not in body
    if call_to_action and call_to_action not in final_body:
        final_body += f"\n\n{call_to_action}"

    # Sign-off if sender provided and not in body
    if sender_name and sender_name not in final_body:
        sign_offs = {
            "friendly": "Best,",
            "persuasive": "Looking forward to speaking,",
            "concise": "Thanks,",
            "professional": "Best regards,",
        }
        sign_off = sign_offs.get(tone.lower(), "Best regards,")
        final_body += f"\n\n{sign_off}\n{sender_name}"

    # Generate preview snippet (first 100 characters of body text without greetings/newlines)
    flat_body = " ".join(final_body.split())
    preview_text = flat_body[:100] + ("..." if len(flat_body) > 100 else "")

    return {
        "status": "draft_created",
        "to": clean_to,
        "recipient_name": recipient_name or "",
        "subject": final_subject,
        "body": final_body,
        "preview_text": preview_text,
        "tone": tone.lower(),
        "tokens_applied": list(ctx.keys()),
    }
