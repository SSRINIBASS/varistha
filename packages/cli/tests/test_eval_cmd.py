"""Unit tests for Varistha CLI evaluation commands."""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any

import httpx
from click.testing import CliRunner
from varistha_cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _mock_eval_suites_list_response() -> dict[str, Any]:
    return {
        "suites": [
            {
                "id": str(uuid.uuid4()),
                "name": "sales-researcher-evals",
                "agent_id": str(uuid.uuid4()),
                "eval_type": "offline",
                "description": "Evaluates lead qualification.",
                "config": {
                    "evaluators": [{"name": "exact-match", "type": "exact-match"}],
                    "cases": [{"id": "c1", "name": "Basic Case"}],
                },
                "created_at": "2026-10-16T00:00:00Z",
                "updated_at": "2026-10-16T00:00:00Z",
            }
        ],
        "total": 1,
    }


def _mock_eval_run_response_passed() -> dict[str, Any]:
    suite_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    return {
        "id": run_id,
        "suite_id": suite_id,
        "agent_version_id": str(uuid.uuid4()),
        "status": "completed",
        "total_cases": 2,
        "passed_cases": 2,
        "pass_rate": 1.0,
        "duration_ms": 320,
        "trigger": "cli",
        "error_message": None,
        "results": [
            {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "case_id": "c1",
                "case_name": "Valid Prospect Case",
                "passed": True,
                "score": 1.0,
                "evaluator_name": "exact-match",
                "evaluator_type": "exact-match",
                "latency_ms": 150,
                "failure_reason": None,
            },
            {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "case_id": "c2",
                "case_name": "Email Format Case",
                "passed": True,
                "score": 1.0,
                "evaluator_name": "regex-eval",
                "evaluator_type": "regex",
                "latency_ms": 170,
                "failure_reason": None,
            },
        ],
    }


def _mock_eval_run_response_failed() -> dict[str, Any]:
    suite_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    return {
        "id": run_id,
        "suite_id": suite_id,
        "agent_version_id": str(uuid.uuid4()),
        "status": "completed",
        "total_cases": 2,
        "passed_cases": 1,
        "pass_rate": 0.5,
        "duration_ms": 280,
        "trigger": "cli",
        "error_message": None,
        "results": [
            {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "case_id": "c1",
                "case_name": "Valid Prospect Case",
                "passed": True,
                "score": 1.0,
                "evaluator_name": "exact-match",
                "evaluator_type": "exact-match",
                "latency_ms": 140,
                "failure_reason": None,
            },
            {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "case_id": "c2",
                "case_name": "Negative Grounding Case",
                "passed": False,
                "score": 0.2,
                "evaluator_name": "grounding-eval",
                "evaluator_type": "grounding",
                "latency_ms": 140,
                "failure_reason": "Grounding ratio 0.20 is below threshold 0.50.",
            },
        ],
    }


def test_eval_list_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha eval list` displays table of eval suites."""

    def mock_get(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=_mock_eval_suites_list_response(),
            request=httpx.Request("GET", "http://localhost:8000/api/v1/evals/suites"),
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    runner = CliRunner(env={"COLUMNS": "200"})
    result = runner.invoke(cli, ["eval", "list"])
    assert result.exit_code == 0
    assert "sales-researcher-evals" in result.output
    assert "offline" in result.output


def test_eval_list_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha eval list --json` outputs raw JSON."""

    def mock_get(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=_mock_eval_suites_list_response(),
            request=httpx.Request("GET", "http://localhost:8000/api/v1/evals/suites"),
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    runner = CliRunner(env={"COLUMNS": "200"})
    result = runner.invoke(cli, ["eval", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == 1
    assert data["suites"][0]["name"] == "sales-researcher-evals"


def test_eval_run_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha eval run <suite_id>` passes when pass rate >= 80%."""
    target_suite_id = str(uuid.uuid4())

    def mock_post(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=_mock_eval_run_response_passed(),
            request=httpx.Request(
                "POST", f"http://localhost:8000/api/v1/evals/suites/{target_suite_id}/execute"
            ),
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    runner = CliRunner(env={"COLUMNS": "200"})
    result = runner.invoke(cli, ["eval", "run", target_suite_id])
    assert result.exit_code == 0
    assert "Offline Evaluation Summary" in result.output
    assert "100.0%" in result.output
    assert "2 / 2 passed" in result.output
    assert "Valid Prospect Case" in result.output


def test_eval_run_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha eval run <suite_id>` exits with code 1 when pass rate < 80%."""
    target_suite_id = str(uuid.uuid4())

    def mock_post(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=_mock_eval_run_response_failed(),
            request=httpx.Request(
                "POST", f"http://localhost:8000/api/v1/evals/suites/{target_suite_id}/execute"
            ),
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    runner = CliRunner(env={"COLUMNS": "200"})
    result = runner.invoke(cli, ["eval", "run", target_suite_id])
    assert result.exit_code == 1
    assert "50.0%" in result.output
    assert "FAIL" in result.output
    assert "Grounding ratio 0.20 is below threshold 0.50." in result.output


def test_eval_run_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha eval run <file.yaml>` executes suite from local spec file."""
    yaml_content = """
apiVersion: varistha/v1
kind: EvalSuite
metadata:
  name: lead-evals
  agent: sales-lead
spec:
  evaluators:
    - name: exact
      type: exact-match
  cases:
    - id: c1
      name: Sample Case
      input:
        prompt: test
      expected: test
"""
    eval_file = tmp_path / "lead_evals.yaml"
    eval_file.write_text(yaml_content, encoding="utf-8")

    agent_id = str(uuid.uuid4())
    suite_id = str(uuid.uuid4())

    def mock_get(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        if "/api/v1/agents/sales-lead" in url:
            return httpx.Response(
                status_code=200,
                json={"id": agent_id, "name": "sales-lead"},
                request=httpx.Request("GET", url),
            )
        if "/api/v1/evals/suites" in url:
            return httpx.Response(
                status_code=200,
                json={"suites": [{"id": suite_id, "name": "lead-evals"}], "total": 1},
                request=httpx.Request("GET", url),
            )
        return httpx.Response(status_code=404, request=httpx.Request("GET", url))

    def mock_post(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=_mock_eval_run_response_passed(),
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "get", mock_get)
    monkeypatch.setattr(httpx.Client, "post", mock_post)

    runner = CliRunner()
    result = runner.invoke(cli, ["eval", "run", str(eval_file)])
    assert result.exit_code == 0
    assert "Offline Evaluation Summary" in result.output


def test_eval_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI prints connection error cleanly when server unreachable."""

    def mock_get(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    runner = CliRunner()
    result = runner.invoke(cli, ["eval", "list"])
    assert result.exit_code == 1
    assert "Could not connect" in result.output
