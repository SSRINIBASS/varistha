"""Integration tests verifying end-to-end OpenTelemetry tracing during agent runs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import AsyncClient


def _make_spec(name: str = "traced-agent") -> dict[str, Any]:
    """Return a valid raw AgentSpec dict for testing."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "eng@startup.io",
            "stage": "prototype",
            "version": "1.0.0",
        },
        "spec": {
            "role": "Agent with automatic tracing",
            "model": {"primary": "gpt-4o"},
            "instructions": "Execute test with trace spans.",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }


async def test_agent_run_emits_and_persists_spans(async_client: AsyncClient) -> None:
    """Invoking an agent run creates agent.run root span and llm.call child span."""
    # 1. Register agent
    spec = _make_spec(name="telemetry-agent")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201

    # 2. Trigger run
    run_resp = await async_client.post(
        "/api/v1/agents/telemetry-agent/runs",
        json={"input": {"task": "verify telemetry spans"}},
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    run_id = run_data["id"]

    # 3. Retrieve spans via observability endpoint
    spans_resp = await async_client.get(f"/api/v1/runs/{run_id}/spans")
    assert spans_resp.status_code == 200
    spans_data = spans_resp.json()

    assert spans_data["total"] >= 2
    span_names = [s["name"] for s in spans_data["items"]]
    assert "agent.run" in span_names
    assert "llm.call" in span_names

    # Check root span details
    root_span = next(s for s in spans_data["items"] if s["name"] == "agent.run")
    assert root_span["run_id"] == run_id
    assert root_span["parent_span_id"] is None
    assert root_span["status"] == "OK"
    assert root_span["attributes"]["varistha.agent_name"] == "telemetry-agent"
    assert root_span["attributes"]["varistha.stage"] == "prototype"
    assert root_span["attributes"]["varistha.autonomy"] == "L1"

    # Check child llm span details
    llm_span = next(s for s in spans_data["items"] if s["name"] == "llm.call")
    assert llm_span["run_id"] == run_id
    assert llm_span["parent_span_id"] == root_span["span_id"]
    assert llm_span["status"] == "OK"
    assert llm_span["attributes"]["gen_ai.system"] == "mock"
    assert llm_span["attributes"]["gen_ai.request.model"] == "gpt-4o"
    assert int(llm_span["attributes"]["gen_ai.usage.total_tokens"]) > 0
    assert llm_span["attributes"]["varistha.cost_usd"] > 0
