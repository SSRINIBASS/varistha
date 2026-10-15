"""Tests for `varistha diff` command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from click.testing import CliRunner

MOCK_DIFF_BREAKING: dict[str, Any] = {
    "from_version": "0.1.0",
    "to_version": "0.2.0",
    "has_changes": True,
    "has_breaking_changes": True,
    "summary": {
        "total": 3,
        "added": 1,
        "removed": 1,
        "modified": 1,
        "breaking": 2,
    },
    "entries": [
        {
            "field": "spec.autonomy",
            "change_type": "modified",
            "old_value": "L1",
            "new_value": "L2",
            "is_breaking": True,
            "breaking_reason": "Autonomy escalated from L1 to L2",
            "description": "Autonomy escalated to L2.",
        },
        {
            "field": "spec.plugins.web-search",
            "change_type": "removed",
            "old_value": {"name": "web-search", "enabled": True},
            "new_value": None,
            "is_breaking": True,
            "breaking_reason": "Plugin 'web-search' removed",
            "description": "Plugin removed.",
        },
        {
            "field": "spec.budget.max_usd_per_day",
            "change_type": "modified",
            "old_value": 10.0,
            "new_value": 20.0,
            "is_breaking": False,
            "breaking_reason": None,
            "description": "Daily budget increased.",
        },
    ],
    "breaking_entries": [
        {
            "field": "spec.autonomy",
            "breaking_reason": "Autonomy escalated from L1 to L2",
        },
        {
            "field": "spec.plugins.web-search",
            "breaking_reason": "Plugin 'web-search' removed",
        },
    ],
}

MOCK_DIFF_SAFE: dict[str, Any] = {
    "from_version": "0.1.0",
    "to_version": "0.1.1",
    "has_changes": True,
    "has_breaking_changes": False,
    "summary": {
        "total": 1,
        "added": 0,
        "removed": 0,
        "modified": 1,
        "breaking": 0,
    },
    "entries": [
        {
            "field": "spec.role",
            "change_type": "modified",
            "old_value": "Old role",
            "new_value": "New role",
            "is_breaking": False,
            "description": "Role updated.",
        }
    ],
    "breaking_entries": [],
}

MOCK_DIFF_IDENTICAL: dict[str, Any] = {
    "from_version": "0.1.0",
    "to_version": "0.1.0",
    "has_changes": False,
    "has_breaking_changes": False,
    "summary": {"total": 0, "added": 0, "removed": 0, "modified": 0, "breaking": 0},
    "entries": [],
    "breaking_entries": [],
}


def test_diff_missing_arguments(runner: CliRunner) -> None:
    """`varistha diff` with no arguments shows error and exits 1."""
    result = runner.invoke(cli, ["diff"])
    assert result.exit_code == 1
    assert "Invalid Arguments" in result.output


def test_diff_versions_success(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha diff <agent> <v1> <v2>` prints diff and exits 0."""
    def _mock_diff(self: Any, id_or_name: str, v1: str, v2: str) -> dict[str, Any]:
        return MOCK_DIFF_BREAKING

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _mock_diff)

    result = runner.invoke(cli, ["diff", "test-agent", "0.1.0", "0.2.0"])
    assert result.exit_code == 0
    assert "Spec Diff: v0.1.0 -> v0.2.0" in result.output
    assert "WARNING: This diff introduces 2 BREAKING change(s)!" in result.output
    assert "spec.autonomy" in result.output


def test_diff_versions_identical(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Identical versions output 'No differences detected'."""
    def _mock_diff(self: Any, id_or_name: str, v1: str, v2: str) -> dict[str, Any]:
        return MOCK_DIFF_IDENTICAL

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _mock_diff)

    result = runner.invoke(cli, ["diff", "test-agent", "0.1.0", "0.1.0"])
    assert result.exit_code == 0
    assert "No differences detected" in result.output


def test_diff_file_preview_success(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha diff -f <file.yaml>` previews candidate diff."""
    def _mock_preview(
        self: Any, id_or_name: str, spec: dict[str, Any], base_version: str | None = None
    ) -> dict[str, Any]:
        return MOCK_DIFF_SAFE

    monkeypatch.setattr(VaristhaClient, "preview_spec_diff", _mock_preview)

    spec_file = tmp_path / "agent.yaml"
    spec_file.write_text(
        """apiVersion: varistha/v1
kind: Agent
metadata:
  name: preview-agent
  owner: test@example.com
  stage: prototype
  version: 0.1.1
spec:
  role: Updated role
  autonomy: L1
  instructions: ./prompt.md
  model:
    primary: gpt-4o
""",
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["diff", "-f", str(spec_file)])
    assert result.exit_code == 0
    assert "Spec Diff" in result.output
    assert "spec.role" in result.output


def test_diff_strict_fails_on_breaking_changes(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha diff --strict` exits 1 if breaking changes exist."""
    def _mock_diff(self: Any, id_or_name: str, v1: str, v2: str) -> dict[str, Any]:
        return MOCK_DIFF_BREAKING

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _mock_diff)

    result = runner.invoke(cli, ["diff", "test-agent", "0.1.0", "0.2.0", "--strict"])
    assert result.exit_code == 1


def test_diff_strict_passes_on_safe_changes(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha diff --strict` exits 0 if only safe changes exist."""
    def _mock_diff(self: Any, id_or_name: str, v1: str, v2: str) -> dict[str, Any]:
        return MOCK_DIFF_SAFE

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _mock_diff)

    result = runner.invoke(cli, ["diff", "test-agent", "0.1.0", "0.1.1", "--strict"])
    assert result.exit_code == 0



def test_diff_connection_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Report connection error gracefully."""

    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise VaristhaConnectionError("Connection refused")

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _raise)

    result = runner.invoke(cli, ["diff", "test-agent", "0.1.0", "0.2.0"])
    assert result.exit_code == 1
    assert "Connection Error" in result.output


def test_diff_api_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Report API error gracefully."""

    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise VaristhaApiError(404, "Agent 'unknown' not found")

    monkeypatch.setattr(VaristhaClient, "get_version_diff", _raise)

    result = runner.invoke(cli, ["diff", "unknown", "0.1.0", "0.2.0"])
    assert result.exit_code == 1
    assert "API Error (404)" in result.output
