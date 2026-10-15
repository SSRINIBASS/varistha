"""Tests for `varistha apply` command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.main import cli
from varistha_cli.templates import generate_starter_spec

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from click.testing import CliRunner


def test_apply_file_not_found(runner: CliRunner) -> None:
    """`varistha apply -f non_existent.yaml` reports file not found and exits 1."""
    result = runner.invoke(cli, ["apply", "-f", "non_existent.yaml"])
    assert result.exit_code == 1
    assert "Spec file not found" in result.output


def test_apply_invalid_yaml_syntax(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha apply` reports YAML syntax error."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("metadata: [unclosed list", encoding="utf-8")

    result = runner.invoke(cli, ["apply", "-f", str(bad_file)])
    assert result.exit_code == 1
    assert "YAML parsing error" in result.output or "validation failed" in result.output


def test_apply_spec_validation_failure(runner: CliRunner, tmp_path: Path) -> None:
    """`varistha apply` runs local validation and catches schema errors before API call."""
    invalid_file = tmp_path / "invalid.yaml"
    # Missing kind, invalid autonomy
    invalid_file.write_text(
        """apiVersion: varistha/v1
metadata:
  name: test-agent
  owner: not-an-email
spec:
  autonomy: L99
""",
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["apply", "-f", str(invalid_file)])
    assert result.exit_code == 1
    assert "validation failed" in result.output.lower()


def test_apply_creates_new_agent(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha apply` creates new agent when it does not exist."""
    spec_file = tmp_path / "agent.yaml"
    spec_file.write_text(generate_starter_spec(name="brand-new-agent"), encoding="utf-8")

    fake_agent_resp = {
        "id": "11111111-2222-3333-4444-555555555555",
        "name": "brand-new-agent",
        "version": "0.1.0",
        "stage": "prototype",
        "spec": {
            "role": "Test role",
            "autonomy": "L1",
            "model": {"primary": "gpt-4o-mini"},
        },
    }

    # Mock client methods
    def mock_get_none(self: Any, id_or_name: str) -> None:
        return None

    def mock_create(self: Any, spec: dict[str, Any]) -> dict[str, Any]:
        return fake_agent_resp

    monkeypatch.setattr(VaristhaClient, "get_agent", mock_get_none)
    monkeypatch.setattr(VaristhaClient, "create_agent", mock_create)

    result = runner.invoke(cli, ["apply", "-f", str(spec_file)])
    assert result.exit_code == 0
    assert "Created new agent" in result.output
    assert "brand-new-agent" in result.output
    assert "v0.1.0" in result.output


def test_apply_registers_new_version_when_agent_exists(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha apply` registers new version when agent already exists in registry."""
    spec_file = tmp_path / "agent.yaml"
    spec_file.write_text(generate_starter_spec(name="existing-agent"), encoding="utf-8")

    existing_agent = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "name": "existing-agent",
        "current_version": "0.1.0",
    }
    fake_version_resp = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "name": "existing-agent",
        "version": "0.1.0",
        "stage": "prototype",
        "spec": {
            "role": "Test role",
            "autonomy": "L1",
            "model": {"primary": "gpt-4o-mini"},
        },
    }

    def mock_get_existing(self: Any, id_or_name: str) -> dict[str, Any]:
        return existing_agent

    def mock_create_ver(self: Any, id_or_name: str, spec: dict[str, Any]) -> dict[str, Any]:
        return fake_version_resp

    monkeypatch.setattr(VaristhaClient, "get_agent", mock_get_existing)
    monkeypatch.setattr(VaristhaClient, "create_agent_version", mock_create_ver)

    result = runner.invoke(cli, ["apply", "-f", str(spec_file)])
    assert result.exit_code == 0
    assert "Registered version" in result.output
    assert "existing-agent" in result.output


def test_apply_handles_connection_error(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha apply` handles unreachable API server gracefully."""
    spec_file = tmp_path / "agent.yaml"
    spec_file.write_text(generate_starter_spec(name="demo-agent"), encoding="utf-8")

    def mock_get_agent(self: Any, id_or_name: str) -> None:
        raise VaristhaConnectionError("Connection refused to http://localhost:8000")

    monkeypatch.setattr(VaristhaClient, "get_agent", mock_get_agent)

    result = runner.invoke(cli, ["apply", "-f", str(spec_file)])
    assert result.exit_code == 1
    assert "Connection Error" in result.output


def test_apply_handles_api_rejection(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`varistha apply` handles API error response (e.g. 409 Conflict)."""
    spec_file = tmp_path / "agent.yaml"
    spec_file.write_text(generate_starter_spec(name="conflict-agent"), encoding="utf-8")

    def mock_get_found(self: Any, id_or_name: str) -> dict[str, Any]:
        return {"id": "123"}

    monkeypatch.setattr(VaristhaClient, "get_agent", mock_get_found)

    def mock_create_version(self: Any, id_or_name: str, spec: dict[str, Any]) -> None:
        raise VaristhaApiError(409, "Version 0.1.0 already exists and is immutable")

    monkeypatch.setattr(VaristhaClient, "create_agent_version", mock_create_version)

    result = runner.invoke(cli, ["apply", "-f", str(spec_file)])
    assert result.exit_code == 1
    assert "API Rejection" in result.output
    assert "409" in result.output or "immutable" in result.output
