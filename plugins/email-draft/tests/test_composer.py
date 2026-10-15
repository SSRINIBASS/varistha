"""Tests for email-draft plugin."""

from __future__ import annotations

import pytest
from composer import (
    EmailDraftError,
    compose_email_draft,
    interpolate_tokens,
    validate_email_address,
)


def test_validate_email_address() -> None:
    assert validate_email_address("  alice@acme.com ") == "alice@acme.com"
    with pytest.raises(EmailDraftError):
        validate_email_address("invalid-email")
    with pytest.raises(EmailDraftError):
        validate_email_address("")


def test_interpolate_tokens() -> None:
    template = "Hi {{name}}, welcome to {{company}}!"
    rendered = interpolate_tokens(template, {"name": "Bob", "company": "Varistha"})
    assert rendered == "Hi Bob, welcome to Varistha!"


@pytest.mark.asyncio
async def test_compose_email_draft_with_tokens_and_tone() -> None:
    res = await compose_email_draft(
        to="founder@startup.io",
        recipient_name="Sarah Connor",
        subject="Quick question regarding {{topic}}",
        body="I loved reading about your work on {{topic}} at {{company}}.",
        context={"topic": "Agent Governance", "company": "Cyberdyne"},
        tone="persuasive",
        sender_name="Alex River",
        call_to_action="Would you have 15 minutes this Thursday?",
    )

    assert res["status"] == "draft_created"
    assert res["to"] == "founder@startup.io"
    assert res["subject"] == "Quick question regarding Agent Governance"
    assert "Hi Sarah," in res["body"]
    assert "Cyberdyne" in res["body"]
    assert "Would you have 15 minutes this Thursday?" in res["body"]
    assert "Looking forward to speaking,\nAlex River" in res["body"]
    assert len(res["preview_text"]) > 0
    assert "Agent Governance" in res["preview_text"]


@pytest.mark.asyncio
async def test_compose_email_draft_invalid_recipient_raises() -> None:
    with pytest.raises(EmailDraftError):
        await compose_email_draft(
            to="not-an-email",
            subject="Test",
            body="Hello",
        )
