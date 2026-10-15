"""Tests for email-send plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sender import (
    EmailSendError,
    RecipientSuppressedError,
    check_suppression,
    send_email,
    validate_email_address,
)


def test_manifest_declares_requires_approval() -> None:
    manifest_path = Path(__file__).resolve().parents[1] / "plugin.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["name"] == "email-send"
    assert data["requires_approval"] is True


def test_validate_email_address() -> None:
    assert validate_email_address("info@varistha.ai") == "info@varistha.ai"
    with pytest.raises(EmailSendError):
        validate_email_address("invalid")


def test_check_suppression_blocks_opted_out_emails() -> None:
    suppression_list = ["optout@example.com", "@spammy.com", "competitor.org"]

    # Allowed
    check_suppression("allowed@example.com", suppression_list)

    # Direct match blocked
    with pytest.raises(RecipientSuppressedError):
        check_suppression("optout@example.com", suppression_list)

    # Wildcard domain blocked
    with pytest.raises(RecipientSuppressedError):
        check_suppression("ceo@spammy.com", suppression_list)

    # Domain match blocked
    with pytest.raises(RecipientSuppressedError):
        check_suppression("sales@competitor.org", suppression_list)


@pytest.mark.asyncio
async def test_send_email_dry_run_success() -> None:
    res = await send_email(
        to="founder@startup.io",
        subject="Demo Confirmation",
        body="Here is your demo confirmation.",
        from_email="noreply@varistha.ai",
        dry_run=True,
    )

    assert res["status"] == "simulated_sent"
    assert res["recipient"] == "founder@startup.io"
    assert res["sender"] == "noreply@varistha.ai"
    assert res["message_id"].startswith("msg_")
    assert res["compliance_verified"] is True


@pytest.mark.asyncio
async def test_send_email_empty_subject_or_body_rejected() -> None:
    with pytest.raises(EmailSendError):
        await send_email(to="test@varistha.ai", subject="", body="Body")
    with pytest.raises(EmailSendError):
        await send_email(to="test@varistha.ai", subject="Subj", body="")
