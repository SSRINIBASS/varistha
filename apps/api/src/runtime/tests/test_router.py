"""Integration tests for the Run execution API endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from runtime.mock import MockRuntime
from runtime.router import get_runtime

if TYPE_CHECKING:
    from httpx import AsyncClient


def _make_spec(name: str = "worker-agent", version: str = "0.1.0") -> dict[str, Any]:
    """Return a valid raw AgentSpec dict for testing."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "founder@example.com",
            "stage": "prototype",
            "version": version,
        },
        "spec": {
            "role": "Lead extraction agent",
            "model": {"primary": "gpt-4o"},
            "instructions": "Extract business leads.",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }


async def test_trigger_run_success(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id}/runs triggers execution and updates run record."""
    # 1. Register agent
    spec = _make_spec(name="runner-agent")
    create_resp = await async_client.post("/api/v1/agents", json=spec)
    assert create_resp.status_code == 201

    # 2. Trigger run by slug name
    run_resp = await async_client.post(
        "/api/v1/agents/runner-agent/runs",
        json={"input": {"niche": "AI startups"}, "trigger_type": "manual"},
    )

    assert run_resp.status_code == 201
    run_data = run_resp.json()
    assert run_data["status"] == "completed"
    assert run_data["trigger_type"] == "manual"
    assert run_data["input"] == {"niche": "AI startups"}
    assert "result" in run_data["output"]
    assert run_data["cost_usd"] > 0
    assert run_data["total_tokens"] > 0
    assert run_data["started_at"] is not None
    assert run_data["completed_at"] is not None

    run_id = run_data["id"]

    # 3. Retrieve run by UUID
    get_resp = await async_client.get(f"/api/v1/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == run_id
    assert get_resp.json()["status"] == "completed"


async def test_trigger_run_by_uuid(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id}/runs accepts agent UUID."""
    spec = _make_spec(name="uuid-runner")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    agent_id = reg_resp.json()["id"]

    run_resp = await async_client.post(
        f"/api/v1/agents/{agent_id}/runs",
        json={"input": {"test": "data"}},
    )

    assert run_resp.status_code == 201
    assert run_resp.json()["agent_id"] == agent_id
    assert run_resp.json()["status"] == "completed"


async def test_trigger_run_agent_not_found(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id}/runs returns 404 for non-existent agent."""
    resp = await async_client.post(
        "/api/v1/agents/non-existent-agent/runs",
        json={"input": {}},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_trigger_run_with_custom_trigger_type(async_client: AsyncClient) -> None:
    """POST /api/v1/agents/{id}/runs accepts custom trigger type."""
    spec = _make_spec(name="webhook-agent")
    await async_client.post("/api/v1/agents", json=spec)

    resp = await async_client.post(
        "/api/v1/agents/webhook-agent/runs",
        json={"input": {"event": "user.signup"}, "trigger_type": "webhook"},
    )

    assert resp.status_code == 201
    assert resp.json()["trigger_type"] == "webhook"


async def test_trigger_run_with_failure(async_client: AsyncClient) -> None:
    """Run reflects failed status and records error if runtime fails."""
    spec = _make_spec(name="error-agent")
    await async_client.post("/api/v1/agents", json=spec)

    failing_runtime = MockRuntime(should_fail=True, error_message="API quota exceeded")
    from main import app

    app.dependency_overrides[get_runtime] = lambda: failing_runtime

    try:
        resp = await async_client.post(
            "/api/v1/agents/error-agent/runs",
            json={"input": {}},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error"] == "API quota exceeded"
    finally:
        app.dependency_overrides[get_runtime] = lambda: MockRuntime()


async def test_list_runs_for_agent_and_pagination(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id}/runs lists runs chronologically with pagination."""
    spec = _make_spec(name="multi-run-agent")
    await async_client.post("/api/v1/agents", json=spec)

    # Trigger 3 runs
    for i in range(3):
        await async_client.post(
            "/api/v1/agents/multi-run-agent/runs",
            json={"input": {"idx": i}},
        )

    # List with limit 2
    resp = await async_client.get("/api/v1/agents/multi-run-agent/runs?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2

    # Offset 2
    offset_resp = await async_client.get("/api/v1/agents/multi-run-agent/runs?limit=2&offset=2")
    assert offset_resp.status_code == 200
    assert len(offset_resp.json()["items"]) == 1


async def test_list_runs_nonexistent_agent_returns_404(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{id}/runs returns 404 for unknown agent."""
    resp = await async_client.get("/api/v1/agents/ghost/runs")
    assert resp.status_code == 404


async def test_get_run_detail_not_found(async_client: AsyncClient) -> None:
    """GET /api/v1/runs/{id} returns 404 for unknown run UUID."""
    unknown_id = uuid.uuid4()
    resp = await async_client.get(f"/api/v1/runs/{unknown_id}")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


async def test_list_all_runs_and_filters(async_client: AsyncClient) -> None:
    """GET /api/v1/runs lists all runs across agents and supports filtering."""
    spec_a = _make_spec(name="global-run-a")
    spec_b = _make_spec(name="global-run-b")
    res_a = await async_client.post("/api/v1/agents", json=spec_a)
    await async_client.post("/api/v1/agents", json=spec_b)
    agent_a_id = res_a.json()["id"]

    await async_client.post("/api/v1/agents/global-run-a/runs", json={"input": {}})
    await async_client.post("/api/v1/agents/global-run-b/runs", json={"input": {}})

    # All runs
    all_resp = await async_client.get("/api/v1/runs")
    assert all_resp.status_code == 200
    assert all_resp.json()["total"] >= 2

    # Filter by agent_id
    agent_resp = await async_client.get(f"/api/v1/runs?agent_id={agent_a_id}")
    assert agent_resp.status_code == 200
    data = agent_resp.json()
    assert all(r["agent_id"] == agent_a_id for r in data["items"])

    # Filter by status
    status_resp = await async_client.get("/api/v1/runs?status=completed")
    assert status_resp.status_code == 200
    assert all(r["status"] == "completed" for r in status_resp.json()["items"])
