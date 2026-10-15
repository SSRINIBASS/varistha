"""Tests for CLI root entrypoint, client, and display utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
from varistha_cli.client import (
    VaristhaApiError,
    VaristhaClient,
    VaristhaConnectionError,
)
from varistha_cli.display import (
    format_cost,
    format_status,
    format_tokens,
    print_agent_panel,
    print_error,
    print_run_summary,
    print_success,
)
from varistha_cli.main import cli

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_cli_help(runner: CliRunner) -> None:
    """`varistha --help` lists all three core commands."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "apply" in result.output
    assert "run" in result.output


def test_cli_version(runner: CliRunner) -> None:
    """`varistha --version` prints current version."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_custom_api_url(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """`varistha --api-url http://custom:9000 run ...` uses custom URL."""
    captured_urls: list[str] = []

    original_init = VaristhaClient.__init__

    def mock_init(
        self: VaristhaClient, base_url: str = "http://localhost:8000", timeout: float = 30.0
    ) -> None:
        captured_urls.append(base_url)
        original_init(self, base_url=base_url, timeout=timeout)

    def mock_trigger(
        self: Any, id_or_name: str, input_data: dict[str, Any], trigger_type: str
    ) -> dict[str, Any]:
        return {"id": "1", "status": "completed"}

    monkeypatch.setattr(VaristhaClient, "__init__", mock_init)
    monkeypatch.setattr(VaristhaClient, "trigger_run", mock_trigger)

    result = runner.invoke(
        cli, ["--api-url", "http://custom-api:9000", "run", "test-agent", "--no-watch"]
    )
    assert result.exit_code == 0
    assert "http://custom-api:9000" in captured_urls


def test_display_helpers() -> None:
    """Test formatting and display utility functions."""
    assert "COMPLETED" in format_status("completed")
    assert "FAILED" in format_status("failed")
    assert "RUNNING" in format_status("running")
    assert "WAITING_APPROVAL" in format_status("waiting_approval")
    assert "OTHER" in format_status("other")

    assert format_cost(0.005) == "$0.0050"
    assert format_cost(None) == "$0.0000"

    assert format_tokens(1500) == "1,500"
    assert format_tokens(None) == "0"

    # Verify no exceptions during printing
    print_success("Operation completed")
    print_error("Failed to parse", details=["Missing key", "Bad type"])
    print_error("Failed to parse", details="String detail")

    print_agent_panel(
        {
            "id": "123",
            "name": "agent-1",
            "version": "0.1.0",
            "stage": "dev",
            "spec": {"role": "Tester", "autonomy": "L1", "model": {"primary": "gpt-4"}},
        }
    )

    print_run_summary(
        {
            "id": "run-1",
            "agent_id": "agent-1",
            "status": "completed",
            "duration_ms": 500.0,
            "total_tokens": 1200,
            "cost_usd": 0.005,
            "trace_id": "trace-1",
            "output": {"response": "Done!"},
        }
    )

    print_run_summary(
        {
            "id": "run-2",
            "agent_id": "agent-1",
            "status": "failed",
            "error_message": "LLM crashed",
        }
    )


def test_client_methods_with_mock_transport() -> None:
    """Test VaristhaClient HTTP methods with MockTransport."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/diff" in url:
            return httpx.Response(200, json={"has_changes": True, "entries": []})
        if url.endswith("/health"):
            return httpx.Response(200, json={"status": "healthy"})
        if "/versions" in url and request.method == "POST":
            return httpx.Response(201, json={"id": "found-1", "version": "0.2.0"})
        if "/runs" in url and request.method == "POST":
            return httpx.Response(201, json={"id": "run-1", "status": "running"})
        if "/api/v1/runs/run-1" in url:
            return httpx.Response(200, json={"id": "run-1", "status": "completed"})
        if "/api/v1/agents/not-found" in url:
            return httpx.Response(404, json={"detail": "Not found"})
        if "/api/v1/agents/found" in url:
            return httpx.Response(200, json={"id": "found-1", "name": "found"})
        if url.endswith("/api/v1/agents") and request.method == "POST":
            return httpx.Response(201, json={"id": "new-1", "name": "new-agent"})
        return httpx.Response(500, json={"error": f"Unknown path: {url}"})

    transport = httpx.MockTransport(handler)

    client = VaristhaClient(base_url="http://test-server")

    def make_client() -> httpx.Client:
        return httpx.Client(transport=transport, base_url="http://test-server")

    client.client = make_client

    assert client.check_health() is True
    assert client.get_agent("not-found") is None
    agent = client.get_agent("found")
    assert agent is not None
    assert agent["id"] == "found-1"

    created = client.create_agent({"name": "new-agent"})
    assert created["id"] == "new-1"

    version = client.create_agent_version("found", {"version": "0.2.0"})
    assert version["version"] == "0.2.0"

    run = client.trigger_run("found", {"query": "test"})
    assert run["id"] == "run-1"

    run_detail = client.get_run("run-1")
    assert run_detail["status"] == "completed"

    diff_ver = client.get_version_diff("found", "0.1.0", "0.2.0")
    assert diff_ver["has_changes"] is True

    diff_preview = client.preview_spec_diff("found", {"spec": {}}, base_version="0.1.0")
    assert diff_preview["has_changes"] is True


def test_client_handles_transport_errors() -> None:
    """Test client error mapping on network connection drop."""

    def failing_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Network is unreachable")

    client = VaristhaClient(base_url="http://unreachable")

    def make_client() -> httpx.Client:
        return httpx.Client(
            transport=httpx.MockTransport(failing_handler), base_url="http://unreachable"
        )

    client.client = make_client

    assert client.check_health() is False
    with pytest.raises(VaristhaConnectionError):
        client.get_agent("any")
    with pytest.raises(VaristhaConnectionError):
        client.create_agent({})
    with pytest.raises(VaristhaConnectionError):
        client.create_agent_version("any", {})
    with pytest.raises(VaristhaConnectionError):
        client.trigger_run("any")
    with pytest.raises(VaristhaConnectionError):
        client.get_run("any")


def test_client_handles_generic_request_errors() -> None:
    """Test client error mapping on generic httpx.RequestError."""

    def request_error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out")

    client = VaristhaClient(base_url="http://timeout")

    def make_client() -> httpx.Client:
        return httpx.Client(
            transport=httpx.MockTransport(request_error_handler), base_url="http://timeout"
        )

    client.client = make_client

    with pytest.raises(VaristhaConnectionError):
        client.get_agent("any")
    with pytest.raises(VaristhaConnectionError):
        client.create_agent({})
    with pytest.raises(VaristhaConnectionError):
        client.create_agent_version("any", {})
    with pytest.raises(VaristhaConnectionError):
        client.trigger_run("any")
    with pytest.raises(VaristhaConnectionError):
        client.get_run("any")


def test_client_api_error_responses() -> None:
    """Test VaristhaClient raises VaristhaApiError on HTTP error codes."""

    def error_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/api/v1/agents/err-agent/versions" in url:
            return httpx.Response(400, json={"detail": "Invalid spec"})
        if url.endswith("/api/v1/agents/err-agent"):
            return httpx.Response(500, text="Internal Server Error")
        if url.endswith("/api/v1/agents"):
            return httpx.Response(422, json={"detail": "Unprocessable"})
        if "/runs" in url and request.method == "POST":
            return httpx.Response(403, json={"detail": "Autonomy ceiling exceeded"})
        if "/runs/err-run" in url:
            return httpx.Response(404, json={"detail": "Run not found"})
        return httpx.Response(500, text="Fail")

    client = VaristhaClient(base_url="http://error-test")

    def make_client() -> httpx.Client:
        return httpx.Client(
            transport=httpx.MockTransport(error_handler), base_url="http://error-test"
        )

    client.client = make_client

    with pytest.raises(VaristhaApiError) as exc_get:
        client.get_agent("err-agent")
    assert exc_get.value.status_code == 500

    with pytest.raises(VaristhaApiError) as exc_create:
        client.create_agent({"name": "err"})
    assert exc_create.value.status_code == 422

    with pytest.raises(VaristhaApiError) as exc_ver:
        client.create_agent_version("err-agent", {"version": "2.0.0"})
    assert exc_ver.value.status_code == 400

    with pytest.raises(VaristhaApiError) as exc_run:
        client.trigger_run("err-agent", {})
    assert exc_run.value.status_code == 403

    with pytest.raises(VaristhaApiError) as exc_get_run:
        client.get_run("err-run")
    assert exc_get_run.value.status_code == 404
    assert exc_get_run.value.status_code == 404


def test_display_json_nested_output() -> None:
    """Test print_run_summary with arbitrary nested JSON output."""
    print_run_summary(
        {
            "id": "run-nested",
            "agent_id": "agent-nested",
            "status": "completed",
            "output": {"leads": [{"name": "Lead A", "score": 95}, {"name": "Lead B", "score": 88}]},
        }
    )
    print_run_summary(
        {
            "id": "run-str",
            "agent_id": "agent-str",
            "status": "completed",
            "output": "Plain text summary without dictionary wrapper",
        }
    )
