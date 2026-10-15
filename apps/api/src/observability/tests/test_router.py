"""Integration tests for OpenTelemetry OTLP receiver and span query endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import AsyncClient


def _make_spec(name: str = "trace-agent") -> dict[str, Any]:
    """Return a valid raw AgentSpec dict for testing."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "dev@startup.io",
            "stage": "prototype",
            "version": "0.1.0",
        },
        "spec": {
            "role": "Trace test agent",
            "model": {"primary": "gpt-4o"},
            "instructions": "Echo input.",
            "autonomy": "L1",
            "triggers": [{"type": "manual"}],
        },
    }


async def _create_test_run(client: AsyncClient, agent_name: str = "trace-agent") -> str:
    """Register an agent and trigger a run, returning the run ID."""
    spec = _make_spec(name=agent_name)
    reg_resp = await client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201

    run_resp = await client.post(
        f"/api/v1/agents/{agent_name}/runs",
        json={"input": {"test": "data"}},
    )
    assert run_resp.status_code == 201
    return str(run_resp.json()["id"])


async def test_otlp_ingest_and_query_run_spans(async_client: AsyncClient) -> None:
    """POST /v1/traces persists spans and GET /api/v1/runs/{id}/spans returns ordered list."""
    run_id = await _create_test_run(async_client, "agent-a")
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"

    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "varistha-agent"}},
                        {"key": "varistha.run_id", "value": {"stringValue": run_id}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "varistha.runtime", "version": "0.1.0"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": "00f067aa0ba902b7",
                                "name": "agent.run",
                                "kind": 1,
                                "startTimeUnixNano": "1729000000000000000",
                                "endTimeUnixNano": "1729000002000000000",
                                "attributes": [
                                    {"key": "varistha.cost_usd", "value": {"doubleValue": 0.05}},
                                ],
                                "status": {"code": 1},
                            },
                            {
                                "traceId": trace_id,
                                "spanId": "5fb397be34d23b0f",
                                "parentSpanId": "00f067aa0ba902b7",
                                "name": "llm.call",
                                "kind": 3,
                                "startTimeUnixNano": "1729000001000000000",
                                "endTimeUnixNano": "1729000002000000000",
                                "attributes": [
                                    {
                                        "key": "gen_ai.request.model",
                                        "value": {"stringValue": "gpt-4o"},
                                    },
                                ],
                                "status": {"code": 1},
                            },
                        ],
                    }
                ],
            }
        ]
    }

    # 1. Ingest via standard OTLP endpoint
    ingest_resp = await async_client.post("/v1/traces", json=payload)
    assert ingest_resp.status_code == 200
    assert ingest_resp.json() == {"partialSuccess": {}}

    # 2. Query spans for run
    spans_resp = await async_client.get(f"/api/v1/runs/{run_id}/spans")
    assert spans_resp.status_code == 200
    spans_data = spans_resp.json()
    assert spans_data["total"] >= 2

    # Verify chronological ordering & fields of ingested trace spans
    ingested_spans = [s for s in spans_data["items"] if s["trace_id"] == trace_id]
    assert len(ingested_spans) == 2

    root_span = next(s for s in ingested_spans if s["span_id"] == "00f067aa0ba902b7")
    assert root_span["name"] == "agent.run"
    assert root_span["parent_span_id"] is None
    assert root_span["duration_ms"] == 2000.0
    assert root_span["attributes"]["varistha.cost_usd"] == 0.05

    child_span = next(s for s in ingested_spans if s["span_id"] == "5fb397be34d23b0f")
    assert child_span["name"] == "llm.call"
    assert child_span["parent_span_id"] == "00f067aa0ba902b7"
    assert child_span["duration_ms"] == 1000.0


async def test_otlp_api_alias_and_trace_detail_query(async_client: AsyncClient) -> None:
    """POST /api/v1/traces alias works and GET /api/v1/traces/{id} returns trace hierarchy."""
    run_id = await _create_test_run(async_client, "agent-b")
    trace_id = "e457b5a2e4d86bd170e2000000000001"

    payload = {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": "1111000011110000",
                                "name": "root-step",
                                "kind": 1,
                                "startTimeUnixNano": "1729000010000000000",
                                "endTimeUnixNano": "1729000015000000000",
                                "attributes": [
                                    {"key": "varistha.run_id", "value": {"stringValue": run_id}}
                                ],
                            }
                        ]
                    }
                ]
            }
        ]
    }

    alias_resp = await async_client.post("/api/v1/traces", json=payload)
    assert alias_resp.status_code == 200

    # Query trace detail
    trace_resp = await async_client.get(f"/api/v1/traces/{trace_id}")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["trace_id"] == trace_id
    assert trace_data["run_id"] == run_id
    assert trace_data["total_spans"] == 1
    assert trace_data["root_span"]["name"] == "root-step"


async def test_otlp_ingest_with_header_fallback_run_id(async_client: AsyncClient) -> None:
    """Verify X-Varistha-Run-Id header is used when span lacks varistha.run_id."""
    run_id = await _create_test_run(async_client, "agent-c")
    trace_id = "aabbccddeeff00112233445566778899"

    payload = {
        "spans": [
            {
                "traceId": trace_id,
                "spanId": "9988776655443322",
                "name": "header-linked-span",
                "startTimeUnixNano": "1729000020000000000",
            }
        ]
    }

    resp = await async_client.post(
        "/v1/traces",
        json=payload,
        headers={"X-Varistha-Run-Id": run_id},
    )
    assert resp.status_code == 200

    spans_resp = await async_client.get(f"/api/v1/runs/{run_id}/spans")
    assert spans_resp.status_code == 200
    assert spans_resp.json()["total"] >= 1
    header_span = next(
        (s for s in spans_resp.json()["items"] if s["name"] == "header-linked-span"),
        None,
    )
    assert header_span is not None
    assert header_span["span_id"] == "9988776655443322"


async def test_otlp_ingest_missing_run_id_returns_422(async_client: AsyncClient) -> None:
    """POST /v1/traces returns 422 when run_id cannot be found or resolved."""
    payload = {
        "spans": [
            {
                "traceId": "ffffffffffffffffffffffffffffffff",
                "spanId": "eeeeeeeeeeeeeeee",
                "name": "orphan-span",
            }
        ]
    }
    resp = await async_client.post("/v1/traces", json=payload)
    assert resp.status_code == 422
    assert "missing required varistha.run_id" in resp.json()["detail"]


async def test_otlp_ingest_nonexistent_run_id_returns_404(async_client: AsyncClient) -> None:
    """POST /v1/traces returns 404 when referenced run does not exist in DB."""
    fake_run_id = str(uuid.uuid4())
    payload = {
        "spans": [
            {
                "traceId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "spanId": "bbbbbbbbbbbbbbbb",
                "name": "missing-run-span",
                "attributes": [{"key": "varistha.run_id", "value": {"stringValue": fake_run_id}}],
            }
        ]
    }
    resp = await async_client.post("/v1/traces", json=payload)
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


async def test_trace_detail_not_found(async_client: AsyncClient) -> None:
    """GET /api/v1/traces/{unknown} returns 404."""
    resp = await async_client.get("/api/v1/traces/unknown-trace-id")
    assert resp.status_code == 404


async def test_list_spans_invalid_uuid(async_client: AsyncClient) -> None:
    """GET /api/v1/runs/{invalid}/spans returns 400."""
    resp = await async_client.get("/api/v1/runs/not-a-uuid/spans")
    assert resp.status_code == 400
