"""Security and privacy utilities for redacting secrets and PII from telemetry."""

from __future__ import annotations

import re
from typing import Any

# Sensitive attribute/key patterns (excluding LLM usage token counts)
_SENSITIVE_KEY_REGEX = re.compile(
    r"(password|secret|api[_-]?key|auth|authorization|private[_-]?key|cookie|credential|"
    r"(?:^|[._-])(?:access|refresh|api|auth|secret|bearer|session|jwt)?[_-]?token(?:$|[._-]))",
    re.IGNORECASE,
)

# Email address regex (RFC 5322 compatible simplified pattern)
_EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Bearer token regex
_BEARER_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)


def redact_string(value: str) -> str:
    """Mask known sensitive patterns (emails, tokens) in a string value."""
    result = _BEARER_REGEX.sub(r"\1[REDACTED_TOKEN]", value)
    return _EMAIL_REGEX.sub("[REDACTED_EMAIL]", result)


def redact_value(value: Any, key_name: str | None = None) -> Any:
    """Recursively redact secrets and PII from a value."""
    if (
        key_name
        and not key_name.endswith("tokens")
        and "usage" not in key_name.lower()
        and _SENSITIVE_KEY_REGEX.search(key_name)
    ):
        return "[REDACTED_SECRET]"

    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, dict):
        return {k: redact_value(v, key_name=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)

    return value


def redact_attributes(attrs: dict[str, Any] | None) -> dict[str, Any]:
    """Redact secrets and PII from a dictionary of span attributes."""
    if not attrs:
        return {}
    return {k: redact_value(v, key_name=k) for k, v in attrs.items()}
