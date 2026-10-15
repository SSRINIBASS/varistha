"""Unit tests for the Spec Diffing Engine (packages/spec/src/diff.py)."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from diff import ChangeType, diff_specs
from validator import validate_spec

BASE_SPEC_DICT: dict[str, Any] = {
    "apiVersion": "varistha/v1",
    "kind": "Agent",
    "metadata": {
        "name": "lead-researcher",
        "owner": "founder@example.com",
        "stage": "prototype",
        "version": "0.3.0",
    },
    "spec": {
        "role": "Find and qualify B2B leads matching our ICP, draft a personalised first touch.",
        "model": {
            "primary": "gpt-4o",
            "fallback": "ollama/llama3",
        },
        "instructions": "./prompts/lead-researcher.md",
        "plugins": [
            {"name": "web-fetch", "enabled": True},
            {"name": "web-search", "enabled": True},
            {"name": "email-draft", "enabled": True},
            {"name": "email-send", "enabled": False},
        ],
        "autonomy": "L1",
        "guardrails": {
            "input": ["pii-redact", "injection-scan"],
            "output": ["schema-valid", "no-unverified-claims"],
            "tools": ["outbound-needs-approval", "rate-limit-50-per-day"],
        },
        "budget": {
            "max_usd_per_run": 0.50,
            "max_usd_per_day": 10.00,
        },
        "triggers": [
            {"type": "schedule", "cron": "0 9 * * 1-5"},
            {"type": "manual"},
        ],
        "evals": {
            "suite": "./evals/lead-researcher.yaml",
            "min_pass_rate": 0.85,
        },
    },
}


def _get_base_spec() -> dict[str, Any]:
    return copy.deepcopy(BASE_SPEC_DICT)


def test_diff_identical_specs():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()

    result = diff_specs(spec1, spec2)
    assert not result.has_changes
    assert not result.has_breaking_changes
    assert result.summary["total"] == 0
    assert result.summary["breaking"] == 0
    assert len(result.entries) == 0
    assert len(result.breaking_entries) == 0
    assert result.from_version == "0.3.0"
    assert result.to_version == "0.3.0"


def test_diff_metadata_non_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["metadata"]["version"] = "0.3.1"
    spec2["metadata"]["owner"] = "engineering@example.com"
    spec2["metadata"]["stage"] = "staging"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    assert result.summary["modified"] == 3
    assert result.summary["breaking"] == 0
    assert result.from_version == "0.3.0"
    assert result.to_version == "0.3.1"


def test_diff_metadata_name_change_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["metadata"]["name"] = "lead-qualifier"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes
    name_entry = next(e for e in result.entries if e.field == "metadata.name")
    assert name_entry.is_breaking
    assert name_entry.breaking_reason is not None


def test_diff_role_and_instructions_modified():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["role"] = "New updated role for lead generation."
    spec2["spec"]["instructions"] = "./prompts/v2-prompts.md"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    assert result.summary["modified"] == 2
    assert result.summary["breaking"] == 0


def test_diff_autonomy_escalation_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["autonomy"] = "L2"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.autonomy")
    assert entry.is_breaking
    assert "escalated" in entry.description


def test_diff_autonomy_restriction_is_non_breaking():
    spec1 = _get_base_spec()
    spec1["spec"]["autonomy"] = "L2"
    spec2 = _get_base_spec()
    spec2["spec"]["autonomy"] = "L1"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.autonomy")
    assert not entry.is_breaking
    assert "restricted" in entry.description


def test_diff_model_primary_change_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["model"]["primary"] = "claude-3-5-sonnet-20241022"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.model.primary")
    assert entry.is_breaking
    assert "Primary model changed" in (entry.breaking_reason or "")


def test_diff_model_fallback_change_is_non_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["model"]["fallback"] = "groq/llama3-70b"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.model.fallback")
    assert not entry.is_breaking


def test_diff_plugin_changes():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()

    # Remove email-draft, disable web-search, enable email-send, add crm-export
    spec2["spec"]["plugins"] = [
        {"name": "web-fetch", "enabled": True},
        {"name": "web-search", "enabled": False},  # disabled -> breaking
        {"name": "email-send", "enabled": True},  # enabled -> non-breaking
        {"name": "crm-export", "enabled": True},  # added -> non-breaking
    ]

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes

    # email-draft removed -> breaking
    removed_entry = next(e for e in result.entries if e.field == "spec.plugins.email-draft")
    assert removed_entry.change_type == ChangeType.REMOVED
    assert removed_entry.is_breaking

    # web-search disabled -> breaking
    disabled_entry = next(e for e in result.entries if e.field == "spec.plugins.web-search.enabled")
    assert disabled_entry.change_type == ChangeType.MODIFIED
    assert disabled_entry.is_breaking

    # email-send enabled -> non-breaking
    enabled_entry = next(e for e in result.entries if e.field == "spec.plugins.email-send.enabled")
    assert enabled_entry.change_type == ChangeType.MODIFIED
    assert not enabled_entry.is_breaking

    # crm-export added -> non-breaking
    added_entry = next(e for e in result.entries if e.field == "spec.plugins.crm-export")
    assert added_entry.change_type == ChangeType.ADDED
    assert not added_entry.is_breaking


def test_diff_guardrails_policy_removed_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    # Remove pii-redact from input, add toxic-filter to output
    spec2["spec"]["guardrails"]["input"] = ["injection-scan"]
    spec2["spec"]["guardrails"]["output"].append("toxic-filter")

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes

    removed = next(e for e in result.entries if "pii-redact" in e.field)
    assert removed.change_type == ChangeType.REMOVED
    assert removed.is_breaking

    added = next(e for e in result.entries if "toxic-filter" in e.field)
    assert added.change_type == ChangeType.ADDED
    assert not added.is_breaking


def test_diff_budget_tightened_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    # Reduce run budget from 0.50 to 0.20
    spec2["spec"]["budget"]["max_usd_per_run"] = 0.20
    # Increase day budget from 10.00 to 20.00
    spec2["spec"]["budget"]["max_usd_per_day"] = 20.00

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes

    run_entry = next(e for e in result.entries if e.field == "spec.budget.max_usd_per_run")
    assert run_entry.is_breaking
    assert run_entry.change_type == ChangeType.MODIFIED

    day_entry = next(e for e in result.entries if e.field == "spec.budget.max_usd_per_day")
    assert not day_entry.is_breaking
    assert day_entry.change_type == ChangeType.MODIFIED


def test_diff_budget_removed_is_breaking():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["budget"] = None

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.budget")
    assert entry.change_type == ChangeType.REMOVED
    assert entry.is_breaking


def test_diff_triggers():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    # Remove manual, update cron schedule
    spec2["spec"]["triggers"] = [
        {"type": "schedule", "cron": "0 8 * * 1-5"},
    ]

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes  # manual trigger removed

    removed_trigger = next(e for e in result.entries if e.field == "spec.triggers.manual")
    assert removed_trigger.change_type == ChangeType.REMOVED
    assert removed_trigger.is_breaking

    cron_entry = next(e for e in result.entries if e.field == "spec.triggers.schedule.cron")
    assert cron_entry.change_type == ChangeType.MODIFIED
    assert not cron_entry.is_breaking


def test_diff_evals_changes():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    # Stricter pass rate from 0.85 to 0.95 (breaking)
    spec2["spec"]["evals"]["min_pass_rate"] = 0.95
    spec2["spec"]["evals"]["suite"] = "./evals/v2.yaml"

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes

    rate_entry = next(e for e in result.entries if e.field == "spec.evals.min_pass_rate")
    assert rate_entry.is_breaking

    suite_entry = next(e for e in result.entries if e.field == "spec.evals.suite")
    assert not suite_entry.is_breaking


def test_diff_with_agentspec_objects():
    spec1_obj = validate_spec(_get_base_spec())
    spec2_dict = _get_base_spec()
    spec2_dict["metadata"]["version"] = "0.4.0"
    spec2_obj = validate_spec(spec2_dict)

    result = diff_specs(spec1_obj, spec2_obj)
    assert result.has_changes
    assert not result.has_breaking_changes
    assert result.from_version == "0.3.0"
    assert result.to_version == "0.4.0"


def test_diff_budget_added_from_none():
    spec1 = _get_base_spec()
    spec1["spec"]["budget"] = None
    spec2 = _get_base_spec()

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.budget")
    assert entry.change_type == ChangeType.ADDED
    assert not entry.is_breaking


def test_diff_trigger_added():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["triggers"].append({"type": "webhook"})

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.triggers.webhook")
    assert entry.change_type == ChangeType.ADDED
    assert not entry.is_breaking


def test_diff_evals_removed():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["evals"] = None

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.evals")
    assert entry.change_type == ChangeType.REMOVED
    assert entry.is_breaking


def test_diff_evals_added_from_none():
    spec1 = _get_base_spec()
    spec1["spec"]["evals"] = None
    spec2 = _get_base_spec()

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.evals")
    assert entry.change_type == ChangeType.ADDED
    assert not entry.is_breaking


def test_diff_evals_min_pass_rate_lowered():
    spec1 = _get_base_spec()
    spec2 = _get_base_spec()
    spec2["spec"]["evals"]["min_pass_rate"] = 0.70

    result = diff_specs(spec1, spec2)
    assert result.has_changes
    assert not result.has_breaking_changes
    entry = next(e for e in result.entries if e.field == "spec.evals.min_pass_rate")
    assert entry.change_type == ChangeType.MODIFIED
    assert not entry.is_breaking
    assert "relaxed" in entry.description


def test_diff_invalid_argument_type():
    with pytest.raises(TypeError, match="Expected AgentSpec or dict"):
        diff_specs("not-a-spec", _get_base_spec())  # type: ignore[arg-type]
