"""Tests for `varistha run` command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.main import cli

if TYPE_CHECKING:
    import pytest
    from click.testing import CliRunner


def test_run_nowatch(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --no-watch` triggers run and exits immediately."""
    fake_run = {
        "id": "11111111-2222-3333-4444-555555555555",
        "agent_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "status": "running",
    }

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_run

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent", "--no-watch"])
    assert result.exit_code == 0
    assert "Run triggered" in result.output
    assert "11111111-2222-3333-4444-555555555555" in result.output


def test_run_watch_completed(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --watch` polls until completed."""
    fake_initial = {
        "id": "run-123",
        "agent_id": "agent-123",
        "status": "running",
    }
    fake_completed = {
        "id": "run-123",
        "agent_id": "agent-123",
        "status": "completed",
        "duration_ms": 1250.5,
        "total_tokens": 850,
        "cost_usd": 0.0042,
        "trace_id": "trace-999",
        "output": {"response": "Lead qualification complete. High ICP match."},
    }

    polls = [fake_initial, fake_completed]

    def mock_get_run(self: Any, run_id: str) -> dict[str, Any]:
        if len(polls) > 1:
            return polls.pop(0)
        return polls[0]

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_initial

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)
    monkeypatch.setattr(VaristhaClient, "get_run", mock_get_run)

    result = runner.invoke(cli, ["run", "my-agent", "--interval", "0.01"])
    assert result.exit_code == 0
    assert "completed successfully" in result.output
    assert "run-123" in result.output
    assert "850" in result.output
    assert "trace-999" in result.output
    assert "High ICP match" in result.output


def test_run_watch_failed(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent` exits with code 1 if run fails."""
    fake_failed = {
        "id": "run-err",
        "agent_id": "agent-123",
        "status": "failed",
        "error_message": "Upstream LLM provider timeout",
    }

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_failed

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent"])
    assert result.exit_code == 1
    assert "failed" in result.output
    assert "Upstream LLM provider timeout" in result.output


def test_run_waiting_approval(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent` handles waiting_approval state."""
    fake_waiting = {
        "id": "run-wait",
        "agent_id": "agent-123",
        "status": "waiting_approval",
    }

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_waiting

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent"])
    assert result.exit_code == 0
    assert "waiting for human approval" in result.output


def test_run_json_output(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --json` outputs raw JSON."""
    fake_completed = {
        "id": "run-json",
        "agent_id": "agent-123",
        "status": "completed",
        "total_tokens": 120,
        "cost_usd": 0.001,
        "trace_id": "trace-json",
        "output": "Task succeeded",
    }

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_completed

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["id"] == "run-json"
    assert parsed["status"] == "completed"


def test_run_structured_input(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run` correctly passes JSON input payload."""
    captured_input: list[dict[str, Any]] = []

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        captured_input.append(input_data)
        return {"id": "run-structured", "status": "completed"}

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    json_payload = '{"company": "Acme Corp", "domain": "acme.com"}'
    result = runner.invoke(cli, ["run", "my-agent", "-i", json_payload])
    assert result.exit_code == 0
    assert len(captured_input) == 1
    assert captured_input[0] == {"company": "Acme Corp", "domain": "acme.com"}


def test_run_handles_connection_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run` handles connection error gracefully."""

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> None:
        raise VaristhaConnectionError("Connection refused")

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent"])
    assert result.exit_code == 1
    assert "Connection Error" in result.output


def test_run_handles_api_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run` handles API error response."""

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> None:
        raise VaristhaApiError(404, "Agent 'non-existent' not found")

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "non-existent"])
    assert result.exit_code == 1
    assert "API Error" in result.output


def test_run_nowatch_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --no-watch --json` outputs raw JSON immediately."""
    fake_run = {"id": "run-nowatch-json", "status": "running"}

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return fake_run

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent", "--no-watch", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["id"] == "run-nowatch-json"
    assert parsed["status"] == "running"


def test_run_watch_polling_json_mode(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --watch --json` polls and outputs final JSON."""
    initial = {"id": "poll-json", "status": "running"}
    final = {"id": "poll-json", "status": "completed", "output": {"data": 123}}

    polls = [initial, final]

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return initial

    def mock_get_run(self: Any, run_id: str) -> dict[str, Any]:
        return polls.pop() if len(polls) > 1 else polls[0]

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)
    monkeypatch.setattr(VaristhaClient, "get_run", mock_get_run)

    result = runner.invoke(cli, ["run", "my-agent", "--interval", "0.01", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["id"] == "poll-json"
    assert parsed["status"] == "completed"


def test_run_watch_timeout(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent` exits 1 on polling timeout."""
    initial = {"id": "timeout-run", "status": "running"}

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return initial

    def mock_get_run(self: Any, run_id: str) -> dict[str, Any]:
        return initial

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)
    monkeypatch.setattr(VaristhaClient, "get_run", mock_get_run)

    result = runner.invoke(cli, ["run", "my-agent", "--timeout", "1", "--interval", "0.05"])
    assert result.exit_code == 1
    assert "timed out" in result.output


def test_run_watch_timeout_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent --json` outputs error JSON on timeout."""
    initial = {"id": "timeout-json", "status": "running"}

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return initial

    def mock_get_run(self: Any, run_id: str) -> dict[str, Any]:
        return initial

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)
    monkeypatch.setattr(VaristhaClient, "get_run", mock_get_run)

    result = runner.invoke(
        cli, ["run", "my-agent", "--timeout", "1", "--interval", "0.05", "--json"]
    )
    assert result.exit_code == 1
    parsed = json.loads(result.output)
    assert "timed out" in parsed["error"]


def test_run_watch_polling_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run agent` handles client error while polling."""
    initial = {"id": "poll-err", "status": "running"}

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return initial

    def mock_get_run(self: Any, run_id: str) -> None:
        raise VaristhaApiError(500, "Database connection dropped")

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)
    monkeypatch.setattr(VaristhaClient, "get_run", mock_get_run)

    result = runner.invoke(cli, ["run", "my-agent", "--interval", "0.01"])
    assert result.exit_code == 1
    assert "Polling Error" in result.output


def test_run_invalid_json_fallback(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing invalid json with braces falls back to raw query dict."""
    captured: list[dict[str, Any]] = []

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        captured.append(input_data)
        return {"id": "fallback-run", "status": "completed"}

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent", "-i", "{not valid json}"])
    assert result.exit_code == 0
    assert captured[0] == {"query": "{not valid json}"}


def test_run_api_error_json_mode(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha run` outputs structured JSON when API errors in json mode."""

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> None:
        raise VaristhaApiError(400, "Bad Request", details={"reason": "invalid_model"})

    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(cli, ["run", "my-agent", "--json"])
    assert result.exit_code == 1
    parsed = json.loads(result.output)
    assert "API Error (400)" in parsed["error"]
    assert parsed["details"] == {"reason": "invalid_model"}
