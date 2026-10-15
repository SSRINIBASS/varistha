"""Unit tests for `varistha budget`, `kill`, `resume`, and `emergency-stop` CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from varistha_cli.client import (
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.main import cli

if TYPE_CHECKING:
    import pytest
    from click.testing import CliRunner


def test_budget_command_table(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha budget <agent>` renders rich budget panel."""
    fake_budget: dict[str, Any] = {
        "agent_id": "11111111-2222-3333-4444-555555555555",
        "agent_name": "lead-researcher",
        "is_active": True,
        "kill_switch_tripped": False,
        "kill_switch_reason": None,
        "kill_switch_tripped_at": None,
        "max_usd_per_run": 0.50,
        "max_usd_per_day": 10.00,
        "daily_spend_usd": 2.25,
        "daily_runs_count": 5,
        "daily_budget_remaining_usd": 7.75,
        "daily_budget_utilization_pct": 22.5,
    }

    def mock_get_budget(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_budget

    monkeypatch.setattr(VaristhaClient, "get_agent_budget", mock_get_budget)

    result = runner.invoke(cli, ["budget", "lead-researcher"])
    assert result.exit_code == 0
    assert "Financial Budget & Circuit Breaker — lead-researcher" in result.output
    assert "Today's Spend: $2.2500" in result.output
    assert "Max Budget Per Run: $0.50" in result.output
    assert "Max Budget Per Day: $10.00" in result.output
    assert "22.5%" in result.output


def test_budget_command_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha budget <agent> --json` outputs raw JSON."""
    fake_budget: dict[str, Any] = {
        "agent_id": "11111111-2222-3333-4444-555555555555",
        "agent_name": "lead-researcher",
        "is_active": True,
        "kill_switch_tripped": False,
        "daily_spend_usd": 0.0,
    }

    def mock_get_budget(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_budget

    monkeypatch.setattr(VaristhaClient, "get_agent_budget", mock_get_budget)

    result = runner.invoke(cli, ["budget", "lead-researcher", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["agent_name"] == "lead-researcher"


def test_kill_command(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha kill <agent>` trips kill switch and displays confirmation."""
    fake_kill_resp: dict[str, Any] = {
        "agent_id": "11111111-2222-3333-4444-555555555555",
        "agent_name": "lead-researcher",
        "is_active": False,
        "kill_switch_tripped": True,
        "reason": "Scraper error flood",
        "operator": "alice",
    }

    def mock_kill(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_kill_resp

    monkeypatch.setattr(VaristhaClient, "kill_agent", mock_kill)

    kill_args = ["kill", "lead-researcher", "-r", "Scraper error flood", "-o", "alice"]
    result = runner.invoke(cli, kill_args)
    assert result.exit_code == 0
    assert "EMERGENCY STOP ACTIVATED" in result.output
    assert "Agent lead-researcher has been halted" in result.output


def test_resume_command(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha resume <agent>` clears kill switch and displays confirmation."""
    fake_resume_resp: dict[str, Any] = {
        "agent_id": "11111111-2222-3333-4444-555555555555",
        "agent_name": "lead-researcher",
        "is_active": True,
        "kill_switch_tripped": False,
        "operator": "supervisor",
    }

    def mock_resume(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_resume_resp

    monkeypatch.setattr(VaristhaClient, "resume_agent", mock_resume)

    result = runner.invoke(cli, ["resume", "lead-researcher", "-o", "supervisor"])
    assert result.exit_code == 0
    assert "AGENT RESUMED" in result.output
    assert "Execution re-enabled by operator: supervisor" in result.output


def test_emergency_stop_command(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha emergency-stop` queries and toggles global stop."""
    # Query inactive
    def mock_get_global(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"enabled": False}

    monkeypatch.setattr(VaristhaClient, "get_global_kill_switch", mock_get_global)
    res_query = runner.invoke(cli, ["emergency-stop"])
    assert res_query.exit_code == 0
    assert "GLOBAL EMERGENCY STOP INACTIVE" in res_query.output

    # Enable
    def mock_set_global(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "enabled": True,
            "reason": "Fire drill",
            "operator": "admin",
            "tripped_at": "2026-10-15T18:00:00Z",
        }

    monkeypatch.setattr(VaristhaClient, "set_global_kill_switch", mock_set_global)
    res_enable = runner.invoke(cli, ["emergency-stop", "--enable", "-r", "Fire drill"])
    assert res_enable.exit_code == 0
    assert "PLATFORM EMERGENCY STOP ACTIVE" in res_enable.output
    assert "Fire drill" in res_enable.output


def test_budget_command_connection_error(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`varistha budget` exits with 1 on connection failure."""

    def mock_fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise VaristhaConnectionError("Cannot connect to host")

    monkeypatch.setattr(VaristhaClient, "get_agent_budget", mock_fail)

    result = runner.invoke(cli, ["budget", "some-agent"])
    assert result.exit_code == 1
    assert "Cannot connect to host" in result.output
