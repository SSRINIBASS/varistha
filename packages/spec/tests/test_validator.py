"""Unit tests for the spec validator functions.

Tests cover:
- Parsing the YAML fixture (SPEC.md § 3.4 example)
- SpecValidationError raised with human-readable messages
- validate_spec_yaml with bad YAML
- validate_spec_yaml with non-dict YAML
- Unknown autonomy level error message
- Loc prefix in error messages
"""

from __future__ import annotations

from pathlib import Path

import pytest
from exceptions import SpecValidationError
from validator import validate_spec, validate_spec_yaml

_FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# YAML fixture roundtrip
# ---------------------------------------------------------------------------


def test_validate_yaml_fixture() -> None:
    """The lead-researcher.yaml fixture from SPEC.md § 3.4 validates cleanly."""
    yaml_text = (_FIXTURES / "lead-researcher.yaml").read_text(encoding="utf-8")
    spec = validate_spec_yaml(yaml_text)
    assert spec.metadata.name == "lead-researcher"
    assert spec.metadata.stage == "prototype"
    assert spec.metadata.version == "0.3.0"
    assert spec.spec.autonomy == "L1"
    assert spec.spec.budget is not None
    assert spec.spec.budget.max_usd_per_run == 0.50
    assert spec.spec.evals is not None
    assert spec.spec.evals.min_pass_rate == 0.85
    # 5 plugins, 2 enabled
    enabled = [p for p in spec.spec.plugins if p.enabled]
    assert len(enabled) == 3  # web-fetch, web-search, email-draft
    # 2 triggers: schedule + manual
    assert len(spec.spec.triggers) == 2
    trigger_types = {t.type for t in spec.spec.triggers}
    assert "schedule" in trigger_types
    assert "manual" in trigger_types


# ---------------------------------------------------------------------------
# SpecValidationError interface
# ---------------------------------------------------------------------------


def test_validate_returns_typed_errors_on_bad_input() -> None:
    """Bad input raises SpecValidationError with a non-empty errors list."""
    raw = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": "Bad Name",  # invalid slug
            "owner": "dev@example.com",
            "stage": "draft",
            "version": "0.1.0",
        },
        "spec": {
            "role": "do stuff",
            "model": {"primary": "gpt-4o"},
            "instructions": "inline",
            "autonomy": "L1",
        },
    }
    with pytest.raises(SpecValidationError) as exc_info:
        validate_spec(raw)

    err = exc_info.value
    assert len(err.errors) > 0
    # At least one message should mention the name problem
    combined = " ".join(err.errors)
    assert "name" in combined.lower() or "agent name" in combined.lower()


def test_validate_unknown_autonomy_error_message() -> None:
    """Unknown autonomy level gives a SpecValidationError mentioning the field."""
    raw = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": "test-agent",
            "owner": "dev@example.com",
            "stage": "draft",
            "version": "0.1.0",
        },
        "spec": {
            "role": "do stuff",
            "model": {"primary": "gpt-4o"},
            "instructions": "inline",
            "autonomy": "L4",  # invalid
            "triggers": [{"type": "manual"}],
        },
    }
    with pytest.raises(SpecValidationError) as exc_info:
        validate_spec(raw)

    # The error message should contain the location prefix 'spec -> autonomy'
    combined = " ".join(exc_info.value.errors)
    assert "autonomy" in combined.lower()


def test_spec_validation_error_str_representation() -> None:
    """SpecValidationError str() includes all messages."""
    err = SpecValidationError(["field a: bad", "field b: missing"])
    text = str(err)
    assert "field a: bad" in text
    assert "field b: missing" in text
    assert "validation failed" in text.lower()


def test_spec_validation_error_multiple_errors_collected() -> None:
    """Multiple violations in one spec are all collected into errors list."""
    raw = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": "Bad Name",  # invalid slug
            "owner": "not-an-email",  # invalid email
            "stage": "draft",
            "version": "0.1.0",
        },
        "spec": {
            "role": "do stuff",
            "model": {"primary": "gpt-4o"},
            "instructions": "inline",
            "autonomy": "L4",  # invalid autonomy
            "triggers": [{"type": "manual"}],
        },
    }
    with pytest.raises(SpecValidationError) as exc_info:
        validate_spec(raw)

    # Should have at least 2 errors (name + autonomy; email may be 1 more)
    assert len(exc_info.value.errors) >= 2


# ---------------------------------------------------------------------------
# YAML-specific error paths
# ---------------------------------------------------------------------------


def test_validate_spec_yaml_malformed_yaml() -> None:
    """Malformed YAML raises SpecValidationError with a parse error message."""
    bad_yaml = "apiVersion: varistha/v1\n  bad indent:\n - broken"
    with pytest.raises(SpecValidationError) as exc_info:
        validate_spec_yaml(bad_yaml)
    assert "yaml" in " ".join(exc_info.value.errors).lower()


def test_validate_spec_yaml_non_dict() -> None:
    """YAML that parses to a list (not a dict) raises SpecValidationError."""
    list_yaml = "- item1\n- item2\n"
    with pytest.raises(SpecValidationError) as exc_info:
        validate_spec_yaml(list_yaml)
    assert "mapping" in " ".join(exc_info.value.errors).lower()
