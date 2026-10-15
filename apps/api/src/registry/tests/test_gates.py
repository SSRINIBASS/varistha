"""Unit tests for registry stage promotion gates and transition logic."""

from __future__ import annotations

from typing import Any

from registry.gates import (
    ALLOWED_STAGES,
    evaluate_stage_transition,
    is_valid_transition,
)


def make_spec(
    name: str = "test-agent",
    owner: str = "founder@example.com",
    stage: str = "draft",
    guardrails: dict[str, Any] | None = None,
    budget: dict[str, Any] | None = None,
    evals: dict[str, Any] | None = None,
    triggers: list[dict[str, Any]] | None = None,
    autonomy: str = "L1",
) -> dict[str, Any]:
    """Generate a valid AgentSpec dictionary for testing."""
    spec_data: dict[str, Any] = {
        "role": "Autonomous lead researcher",
        "model": {"primary": "gpt-4o"},
        "instructions": "Research leads.",
        "autonomy": autonomy,
        "triggers": triggers if triggers is not None else [{"type": "manual"}],
    }
    if guardrails is not None:
        spec_data["guardrails"] = guardrails
    if budget is not None:
        spec_data["budget"] = budget
    if evals is not None:
        spec_data["evals"] = evals

    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": owner,
            "stage": stage,
            "version": "0.1.0",
        },
        "spec": spec_data,
    }


def test_allowed_stages() -> None:
    """Ensure all required lifecycle stages are recognized."""
    expected = ["draft", "prototype", "staging", "production", "deprecated", "retired"]
    assert list(ALLOWED_STAGES) == expected


def test_transition_validity() -> None:
    """Ensure sequential progression and backwards rollbacks are valid, but skips are not."""
    # Valid sequential
    assert is_valid_transition("draft", "prototype")
    assert is_valid_transition("prototype", "staging")
    assert is_valid_transition("staging", "production")
    assert is_valid_transition("production", "deprecated")
    assert is_valid_transition("deprecated", "retired")

    # Valid rollbacks
    assert is_valid_transition("production", "staging")
    assert is_valid_transition("staging", "prototype")
    assert is_valid_transition("prototype", "draft")
    assert is_valid_transition("deprecated", "production")

    # Invalid forward skips
    assert not is_valid_transition("draft", "staging")
    assert not is_valid_transition("draft", "production")
    assert not is_valid_transition("prototype", "production")

    # Invalid identical transition
    assert not is_valid_transition("draft", "draft")


def test_draft_to_prototype_fails_without_successful_run() -> None:
    """Draft -> Prototype requires at least one successful run."""
    spec = make_spec(stage="draft")
    runs = [{"status": "failed"}, {"status": "pending"}]

    result = evaluate_stage_transition(
        from_stage="draft",
        to_stage="prototype",
        spec_dict=spec,
        runs=runs,
    )
    assert not result.allowed
    check_names = {c.name: c.passed for c in result.checks}
    assert check_names["spec_valid"] is True
    assert check_names["successful_run"] is False


def test_draft_to_prototype_passes_with_successful_run() -> None:
    """Draft -> Prototype passes when at least one run succeeded."""
    spec = make_spec(stage="draft")
    runs = [{"status": "failed"}, {"status": "success"}]

    result = evaluate_stage_transition(
        from_stage="draft",
        to_stage="prototype",
        spec_dict=spec,
        runs=runs,
    )
    assert result.allowed
    assert all(c.passed for c in result.checks)


def test_prototype_to_staging_fails_without_guardrails_or_evals() -> None:
    """Prototype -> Staging requires owner, guardrails, and eval suite."""
    spec = make_spec(stage="prototype")
    result = evaluate_stage_transition(
        from_stage="prototype",
        to_stage="staging",
        spec_dict=spec,
        runs=[{"status": "success"}],
    )
    assert not result.allowed
    checks = {c.name: c.passed for c in result.checks}
    assert checks["owner_assigned"] is True
    assert checks["guardrails_attached"] is False
    assert checks["eval_suite_present"] is False


def test_prototype_to_staging_passes_when_all_met() -> None:
    """Prototype -> Staging passes with guardrails and eval suite."""
    spec = make_spec(
        stage="prototype",
        guardrails={"input": ["pii-redact"], "output": ["schema-valid"]},
        evals={"suite": "./evals/suite.yaml", "min_pass_rate": 0.85},
    )
    result = evaluate_stage_transition(
        from_stage="prototype",
        to_stage="staging",
        spec_dict=spec,
        runs=[{"status": "success"}],
    )
    assert result.allowed
    assert all(c.passed for c in result.checks)


def test_staging_to_production_fails_without_budget_or_kill_switch() -> None:
    """Staging -> Production requires budget limits and tested kill switch."""
    spec = make_spec(
        stage="staging",
        guardrails={"tools": ["outbound-needs-approval"]},
        evals={"suite": "./evals/suite.yaml", "min_pass_rate": 0.85},
    )
    result = evaluate_stage_transition(
        from_stage="staging",
        to_stage="production",
        spec_dict=spec,
        runs=[{"status": "success"}],
        kill_switch_verified=False,
    )
    assert not result.allowed
    checks = {c.name: c.passed for c in result.checks}
    assert checks["budget_configured"] is False
    assert checks["kill_switch_tested"] is False


def test_staging_to_production_passes_when_all_met() -> None:
    """Staging -> Production passes when budget set, kill switch verified, and runs exist."""
    spec = make_spec(
        stage="staging",
        guardrails={"tools": ["outbound-needs-approval"]},
        evals={"suite": "./evals/suite.yaml", "min_pass_rate": 0.85},
        budget={"max_usd_per_run": 0.50, "max_usd_per_day": 10.0},
    )
    result = evaluate_stage_transition(
        from_stage="staging",
        to_stage="production",
        spec_dict=spec,
        runs=[{"status": "success"}],
        kill_switch_verified=True,
    )
    assert result.allowed
    assert all(c.passed for c in result.checks)


def test_production_to_deprecated_fails_if_active_runs() -> None:
    """Production -> Deprecated fails if runs are still in progress."""
    spec = make_spec(stage="production")
    result = evaluate_stage_transition(
        from_stage="production",
        to_stage="deprecated",
        spec_dict=spec,
        runs=[{"status": "running"}],
        replacement="lead-researcher-v2",
    )
    assert not result.allowed
    checks = {c.name: c.passed for c in result.checks}
    assert checks["traffic_drained"] is False
    assert checks["replacement_named"] is True


def test_production_to_deprecated_passes_when_drained() -> None:
    """Production -> Deprecated passes when traffic drained and replacement named."""
    spec = make_spec(stage="production")
    result = evaluate_stage_transition(
        from_stage="production",
        to_stage="deprecated",
        spec_dict=spec,
        runs=[{"status": "success"}],
        replacement="lead-researcher-v2",
    )
    assert result.allowed
    assert all(c.passed for c in result.checks)


def test_deprecated_to_retired_requires_secrets_revoked() -> None:
    """Deprecated -> Retired requires confirmation that secrets were revoked."""
    spec = make_spec(stage="deprecated", triggers=[])
    result = evaluate_stage_transition(
        from_stage="deprecated",
        to_stage="retired",
        spec_dict=spec,
        runs=[{"status": "success"}],
        secrets_revoked=False,
    )
    assert not result.allowed
    checks = {c.name: c.passed for c in result.checks}
    assert checks["secrets_revoked"] is False

    # Now verify with secrets_revoked=True
    result_ok = evaluate_stage_transition(
        from_stage="deprecated",
        to_stage="retired",
        spec_dict=spec,
        runs=[{"status": "success"}],
        secrets_revoked=True,
    )
    assert result_ok.allowed
    assert all(c.passed for c in result_ok.checks)


def test_rollback_requires_reason() -> None:
    """Rollbacks require an explanation reason."""
    spec = make_spec(stage="production")
    # No reason -> rejected
    result_no_reason = evaluate_stage_transition(
        from_stage="production",
        to_stage="staging",
        spec_dict=spec,
        runs=[],
        reason=None,
    )
    assert not result_no_reason.allowed
    assert result_no_reason.is_rollback is True

    # With reason -> allowed
    result_with_reason = evaluate_stage_transition(
        from_stage="production",
        to_stage="staging",
        spec_dict=spec,
        runs=[],
        reason="Detected prompt injection vulnerability in production",
    )
    assert result_with_reason.allowed
    assert result_with_reason.is_rollback is True
