"""Unit tests for AgentSpec Pydantic models.

Tests cover:
- Valid full spec (roundtrip through the fixture)
- Valid minimal spec (only required fields)
- Invalid stage value
- Invalid name slug (spaces, uppercase)
- Schedule trigger without cron
- Extra unknown fields rejected
- Budget value <= 0 rejected
- Invalid semver version rejected
- Invalid cron field count rejected
"""

from __future__ import annotations

import pytest
from models import AgentSpec
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_raw() -> dict:  # type: ignore[type-arg]
    """Return the smallest valid raw spec dict."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": "my-agent",
            "owner": "dev@example.com",
            "stage": "draft",
            "version": "0.1.0",
        },
        "spec": {
            "role": "Do something useful.",
            "model": {"primary": "gpt-4o"},
            "instructions": "./prompts/agent.md",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }


# ---------------------------------------------------------------------------
# Valid specs
# ---------------------------------------------------------------------------


def test_valid_minimal_spec() -> None:
    """Minimal required-fields-only spec validates without error."""
    spec = AgentSpec.model_validate(_minimal_raw())
    assert spec.metadata.name == "my-agent"
    assert spec.metadata.stage == "draft"
    assert spec.spec.autonomy == "L1"
    assert spec.spec.model.fallback is None
    assert spec.spec.guardrails is None
    assert spec.spec.budget is None
    assert spec.spec.evals is None


def test_valid_full_spec() -> None:
    """Full spec with all optional fields validates correctly."""
    raw = _minimal_raw()
    raw["metadata"]["stage"] = "prototype"
    raw["metadata"]["version"] = "0.3.0"
    raw["spec"].update(
        {
            "model": {"primary": "gpt-4o", "fallback": "ollama/llama3"},
            "plugins": [
                {"name": "web-fetch", "enabled": True},
                {"name": "email-send", "enabled": False},
            ],
            "guardrails": {
                "input": ["pii-redact"],
                "output": ["schema-valid"],
                "tools": ["outbound-needs-approval"],
            },
            "budget": {"max_usd_per_run": 0.50, "max_usd_per_day": 10.0},
            "triggers": [
                {"type": "schedule", "cron": "0 9 * * 1-5"},
                {"type": "manual"},
            ],
            "evals": {"suite": "./evals/agent.yaml", "min_pass_rate": 0.85},
        }
    )
    spec = AgentSpec.model_validate(raw)
    assert spec.spec.model.fallback == "ollama/llama3"
    assert len(spec.spec.plugins) == 2
    assert spec.spec.budget is not None
    assert spec.spec.budget.max_usd_per_run == 0.50
    assert spec.spec.evals is not None
    assert spec.spec.evals.min_pass_rate == 0.85


# ---------------------------------------------------------------------------
# Invalid metadata
# ---------------------------------------------------------------------------


def test_invalid_stage_rejected() -> None:
    """Unknown lifecycle stage raises ValidationError."""
    raw = _minimal_raw()
    raw["metadata"]["stage"] = "released"  # not a valid stage
    with pytest.raises(Exception, match="stage"):
        AgentSpec.model_validate(raw)


def test_invalid_name_with_spaces() -> None:
    """Agent name containing spaces is rejected."""
    raw = _minimal_raw()
    raw["metadata"]["name"] = "my agent"
    with pytest.raises(Exception, match="valid agent name"):
        AgentSpec.model_validate(raw)


def test_invalid_name_uppercase() -> None:
    """Agent name containing uppercase letters is rejected."""
    raw = _minimal_raw()
    raw["metadata"]["name"] = "MyAgent"
    with pytest.raises(Exception, match="valid agent name"):
        AgentSpec.model_validate(raw)


def test_invalid_name_starts_with_hyphen() -> None:
    """Agent name starting with a hyphen is rejected."""
    raw = _minimal_raw()
    raw["metadata"]["name"] = "-bad-name"
    with pytest.raises(Exception, match="valid agent name"):
        AgentSpec.model_validate(raw)


def test_invalid_semver_version() -> None:
    """Version that is not semver-compatible is rejected."""
    raw = _minimal_raw()
    raw["metadata"]["version"] = "v1"
    with pytest.raises(Exception, match="valid version"):
        AgentSpec.model_validate(raw)


def test_invalid_owner_email() -> None:
    """Non-email owner value is rejected."""
    raw = _minimal_raw()
    raw["metadata"]["owner"] = "not-an-email"
    with pytest.raises(ValidationError, match="value is not a valid email address"):
        AgentSpec.model_validate(raw)


# ---------------------------------------------------------------------------
# Invalid spec body
# ---------------------------------------------------------------------------


def test_invalid_autonomy_level() -> None:
    """Unknown autonomy level (e.g. L4) is rejected."""
    raw = _minimal_raw()
    raw["spec"]["autonomy"] = "L4"
    with pytest.raises(ValidationError, match=r"autonomy|L4"):
        AgentSpec.model_validate(raw)


def test_schedule_without_cron_rejected() -> None:
    """A schedule trigger without a cron expression is rejected."""
    raw = _minimal_raw()
    raw["spec"]["triggers"] = [{"type": "schedule"}]  # missing cron
    with pytest.raises(Exception, match="cron"):
        AgentSpec.model_validate(raw)


def test_invalid_cron_field_count() -> None:
    """A cron expression with the wrong number of fields is rejected."""
    raw = _minimal_raw()
    raw["spec"]["triggers"] = [{"type": "schedule", "cron": "* * * *"}]  # 4 fields, not 5
    with pytest.raises(Exception, match="cron"):
        AgentSpec.model_validate(raw)


def test_extra_fields_rejected() -> None:
    """Unknown keys at any level cause a hard validation failure."""
    raw = _minimal_raw()
    raw["spec"]["unknown_key"] = "oops"
    with pytest.raises(Exception, match="extra"):
        AgentSpec.model_validate(raw)


def test_budget_zero_run_rejected() -> None:
    """Budget max_usd_per_run of 0 or below is rejected."""
    raw = _minimal_raw()
    raw["spec"]["budget"] = {"max_usd_per_run": 0, "max_usd_per_day": 10}
    with pytest.raises(Exception, match="greater than"):
        AgentSpec.model_validate(raw)


def test_budget_negative_day_rejected() -> None:
    """Budget max_usd_per_day of a negative value is rejected."""
    raw = _minimal_raw()
    raw["spec"]["budget"] = {"max_usd_per_run": 0.50, "max_usd_per_day": -5}
    with pytest.raises(Exception, match="greater than"):
        AgentSpec.model_validate(raw)


def test_eval_pass_rate_above_one_rejected() -> None:
    """min_pass_rate > 1.0 is rejected."""
    raw = _minimal_raw()
    raw["spec"]["evals"] = {"suite": "./evals/agent.yaml", "min_pass_rate": 1.5}
    with pytest.raises(Exception, match="less than or equal"):
        AgentSpec.model_validate(raw)


def test_eval_pass_rate_negative_rejected() -> None:
    """min_pass_rate < 0.0 is rejected."""
    raw = _minimal_raw()
    raw["spec"]["evals"] = {"suite": "./evals/agent.yaml", "min_pass_rate": -0.1}
    with pytest.raises(Exception, match="greater than or equal"):
        AgentSpec.model_validate(raw)


# ---------------------------------------------------------------------------
# API version and kind guards
# ---------------------------------------------------------------------------


def test_wrong_api_version_rejected() -> None:
    """Unsupported apiVersion is rejected."""
    raw = _minimal_raw()
    raw["apiVersion"] = "varistha/v2"
    with pytest.raises(ValidationError, match="varistha/v1"):
        AgentSpec.model_validate(raw)


def test_wrong_kind_rejected() -> None:
    """Kind other than 'Agent' is rejected."""
    raw = _minimal_raw()
    raw["kind"] = "Policy"
    with pytest.raises(ValidationError, match="Agent"):
        AgentSpec.model_validate(raw)
