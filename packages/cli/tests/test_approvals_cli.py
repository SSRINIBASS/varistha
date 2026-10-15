"""Unit tests for `varistha approvals` CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from varistha_cli.client import (
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from click.testing import CliRunner


def test_approvals_list_table(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha approvals list` displays approvals in a styled table."""
    fake_list = {
        "items": [
            {
                "id": "appr-1111",
                "run_id": "run-2222",
                "agent_id": "agent-3333",
                "status": "pending",
                "action_type": "outbound_action",
                "tool_name": "send_email",
                "reviewer": None,
                "created_at": "2026-10-15T12:00:00Z",
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }

    def mock_list(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_list

    monkeypatch.setattr(VaristhaClient, "list_approvals", mock_list)

    result = runner.invoke(cli, ["approvals", "list"])
    assert result.exit_code == 0
    assert "Governance Approvals" in result.output
    assert "appr-1111" in result.output
    assert "send_email" in result.output


def test_approvals_list_json(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha approvals list --json` outputs raw JSON."""
    fake_list: dict[str, Any] = {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
    }

    def mock_list(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_list

    monkeypatch.setattr(VaristhaClient, "list_approvals", mock_list)

    result = runner.invoke(cli, ["approvals", "list", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["total"] == 0


def test_approvals_get(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha approvals get <id>` displays detail view."""
    fake_detail = {
        "id": "appr-1234-5678",
        "run_id": "run-9999",
        "agent_id": "agent-8888",
        "status": "pending",
        "action_type": "tool_call",
        "tool_name": "crm_update",
        "proposed_payload": {"stage": "qualified"},
        "approved_payload": None,
        "diff": None,
        "reviewer": None,
        "feedback": None,
        "created_at": "2026-10-15T12:00:00Z",
    }

    def mock_get(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return fake_detail

    monkeypatch.setattr(VaristhaClient, "get_approval", mock_get)

    result = runner.invoke(cli, ["approvals", "get", "appr-1234-5678"])
    assert result.exit_code == 0
    assert "Approval Detail" in result.output
    assert "crm_update" in result.output
    assert "qualified" in result.output


def test_approvals_approve(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha approvals approve <id>` resolves approval as approved."""
    fake_resolved = {
        "id": "appr-1234-5678",
        "status": "approved",
        "action_type": "tool_call",
        "tool_name": "send_email",
        "proposed_payload": {"to": "lead@corp.com"},
        "approved_payload": {"to": "lead@corp.com"},
        "reviewer": "test-admin",
        "feedback": "Approved for sending",
        "resolved_at": "2026-10-15T12:05:00Z",
    }

    def mock_resolve(
        self: Any, approval_id: str, decision: str, reviewer: str, **kwargs: Any
    ) -> dict[str, Any]:
        assert decision == "approve"
        assert reviewer == "test-admin"
        return fake_resolved

    monkeypatch.setattr(VaristhaClient, "resolve_approval", mock_resolve)

    result = runner.invoke(
        cli,
        [
            "approvals",
            "approve",
            "appr-1234-5678",
            "--reviewer",
            "test-admin",
            "--feedback",
            "Approved for sending",
        ],
    )
    assert result.exit_code == 0
    assert "APPROVED" in result.output


def test_approvals_reject(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha approvals reject <id>` resolves approval as rejected."""
    fake_rejected = {
        "id": "appr-1234-5678",
        "status": "rejected",
        "action_type": "outbound_action",
        "reviewer": "sec-ops",
        "feedback": "Prohibited action",
        "resolved_at": "2026-10-15T12:05:00Z",
    }

    def mock_resolve(
        self: Any, approval_id: str, decision: str, reviewer: str, **kwargs: Any
    ) -> dict[str, Any]:
        assert decision == "reject"
        assert reviewer == "sec-ops"
        return fake_rejected

    monkeypatch.setattr(VaristhaClient, "resolve_approval", mock_resolve)

    result = runner.invoke(
        cli,
        [
            "approvals",
            "reject",
            "appr-1234-5678",
            "--reviewer",
            "sec-ops",
            "--feedback",
            "Prohibited action",
        ],
    )
    assert result.exit_code == 0
    assert "REJECTED" in result.output


def test_approvals_edit(runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`varistha approvals edit <id> --payload ...` sends edited payload."""
    edited_file = tmp_path / "payload.json"
    edited_file.write_text('{"discount": 10}', encoding="utf-8")

    fake_edited = {
        "id": "appr-1234-5678",
        "status": "edited",
        "action_type": "outbound_action",
        "proposed_payload": {"discount": 20},
        "approved_payload": {"discount": 10},
        "diff": {"modified": {"discount": {"old": 20, "new": 10}}},
        "reviewer": "manager",
        "feedback": "Reduced discount",
        "resolved_at": "2026-10-15T12:05:00Z",
    }

    def mock_resolve(
        self: Any,
        approval_id: str,
        decision: str,
        approved_payload: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        assert decision == "edit"
        assert approved_payload == {"discount": 10}
        return fake_edited

    monkeypatch.setattr(VaristhaClient, "resolve_approval", mock_resolve)

    result = runner.invoke(
        cli,
        [
            "approvals",
            "edit",
            "appr-1234-5678",
            "--payload",
            str(edited_file),
            "--reviewer",
            "manager",
        ],
    )
    assert result.exit_code == 0
    assert "EDITED & APPROVED" in result.output


def test_approvals_connection_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Connection errors are gracefully presented to the operator."""

    def mock_fail(*args: Any, **kwargs: Any) -> None:
        raise VaristhaConnectionError("Cannot connect to API")

    monkeypatch.setattr(VaristhaClient, "list_approvals", mock_fail)

    result = runner.invoke(cli, ["approvals", "list"])
    assert result.exit_code == 1
    assert "Connection Error" in result.output
