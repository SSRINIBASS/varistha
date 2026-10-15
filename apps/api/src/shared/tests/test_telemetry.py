"""Tests for shared telemetry, conventions, and secret/PII redaction."""

from __future__ import annotations

from shared.telemetry import (
    GEN_AI_REQUEST_MODEL,
    GEN_AI_SYSTEM,
    VARISTHA_AGENT_ID,
    VARISTHA_RUN_ID,
    get_tracer,
    init_tracer_provider,
    redact_attributes,
    redact_string,
    redact_value,
)


def test_conventions_constants() -> None:
    """Verify semantic conventions match GenAI and Varistha namespaces."""
    assert VARISTHA_RUN_ID == "varistha.run_id"
    assert VARISTHA_AGENT_ID == "varistha.agent_id"
    assert GEN_AI_SYSTEM == "gen_ai.system"
    assert GEN_AI_REQUEST_MODEL == "gen_ai.request.model"


def test_redact_string_masks_emails_and_tokens() -> None:
    """Verify email addresses and Bearer tokens are masked in text."""
    text = "User contact is founder@example.com with Bearer eyJhbGciOiJIUzI1NiJ9.test"
    redacted = redact_string(text)
    assert "founder@example.com" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert "Bearer [REDACTED_TOKEN]" in redacted


def test_redact_attributes_masks_sensitive_keys() -> None:
    """Verify keys containing password, secret, token, api_key are redacted."""
    attrs = {
        "user.email": "alice@startup.io",
        "api_key": "sk-1234567890abcdef",
        "nested": {
            "password": "super-secret-pass",
            "safe_field": "hello world",
            "auth_token": "secret-token-val",
        },
        "list_items": ["contact: bob@example.com", {"client_secret": "my-secret"}],
        "count": 42,
    }

    cleaned = redact_attributes(attrs)

    assert cleaned["user.email"] == "[REDACTED_EMAIL]"
    assert cleaned["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["password"] == "[REDACTED_SECRET]"  # noqa: S105
    assert cleaned["nested"]["auth_token"] == "[REDACTED_SECRET]"  # noqa: S105
    assert cleaned["nested"]["safe_field"] == "hello world"
    assert cleaned["list_items"][0] == "contact: [REDACTED_EMAIL]"
    assert cleaned["list_items"][1]["client_secret"] == "[REDACTED_SECRET]"  # noqa: S105
    assert cleaned["count"] == 42


def test_redact_attributes_empty_or_none() -> None:
    """Verify empty dictionary or None returns empty dict."""
    assert redact_attributes(None) == {}
    assert redact_attributes({}) == {}


def test_redact_value_tuple() -> None:
    """Verify tuples are redacted and preserved."""
    val = redact_value(("alice@corp.com", "clean"))
    assert val == ("[REDACTED_EMAIL]", "clean")


def test_tracer_setup_and_retrieval() -> None:
    """Verify tracer provider can be initialized and tracer returned."""
    provider = init_tracer_provider("test-service")
    assert provider is not None
    tracer = get_tracer("test-tracer")
    assert tracer is not None
