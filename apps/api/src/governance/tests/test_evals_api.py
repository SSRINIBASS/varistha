"""Integration tests for Evaluation API endpoints under /api/v1/evals."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from shared.db.models.agent import Agent, AgentVersion

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def sample_agent_with_version(db_session: AsyncSession) -> tuple[Agent, AgentVersion]:
    agent = Agent(
        name="sales-researcher",
        owner="sales@varistha.io",
        stage="prototype",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        agent_id=agent.id,
        version="0.5.0",
        spec={"apiVersion": "varistha/v1", "kind": "Agent"},
    )
    db_session.add(version)
    await db_session.flush()
    return agent, version


@pytest.mark.asyncio
async def test_create_and_get_eval_suite(
    async_client: AsyncClient,
    sample_agent_with_version: tuple[Agent, AgentVersion],
) -> None:
    agent, _ = sample_agent_with_version

    create_payload = {
        "name": "sales-icp-evals",
        "agent_id": str(agent.id),
        "description": "Verifies ICP score calculations.",
        "config": {
            "evaluators": [{"name": "json-schema-eval", "type": "json-schema"}],
            "cases": [{"id": "c1", "name": "Basic SaaS"}],
        },
    }

    # 1. Create suite
    resp = await async_client.post("/api/v1/evals/suites", json=create_payload)
    assert resp.status_code == 201
    suite_data = resp.json()
    assert suite_data["name"] == "sales-icp-evals"
    assert suite_data["agent_id"] == str(agent.id)
    suite_id = suite_data["id"]

    # 2. Get suite
    get_resp = await async_client.get(f"/api/v1/evals/suites/{suite_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "sales-icp-evals"

    # 3. List suites with filter
    list_resp = await async_client.get(f"/api/v1/evals/suites?agent_id={agent.id}")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert len(list_resp.json()["suites"]) == 1

    # 4. Non-existent suite returns 404
    fake_id = str(uuid.uuid4())
    not_found_resp = await async_client.get(f"/api/v1/evals/suites/{fake_id}")
    assert not_found_resp.status_code == 404


@pytest.mark.asyncio
async def test_eval_run_lifecycle_and_results(
    async_client: AsyncClient,
    sample_agent_with_version: tuple[Agent, AgentVersion],
) -> None:
    agent, version = sample_agent_with_version

    # 1. Create suite
    suite_resp = await async_client.post(
        "/api/v1/evals/suites",
        json={
            "name": "pipeline-evals",
            "agent_id": str(agent.id),
            "description": "Pipeline tests.",
            "config": {},
        },
    )
    assert suite_resp.status_code == 201
    suite_id = suite_resp.json()["id"]

    # 2. Trigger run
    run_resp = await async_client.post(
        "/api/v1/evals/runs",
        json={
            "suite_id": suite_id,
            "agent_version_id": str(version.id),
            "trigger": "ci",
        },
    )
    assert run_resp.status_code == 201
    run_data = run_resp.json()
    run_id = run_data["id"]
    assert run_data["status"] == "running"
    assert run_data["trigger"] == "ci"

    # 3. Record results (2 cases: 1 pass, 1 fail -> 50% pass rate)
    results_payload = [
        {
            "case_id": "case-1",
            "case_name": "Valid SaaS company",
            "input_data": {"domain": "acme.io"},
            "expected_output": {"tier": 1},
            "actual_output": {"tier": 1},
            "passed": True,
            "score": 1.0,
            "evaluator_name": "exact-match",
            "evaluator_type": "exact-match",
            "latency_ms": 120,
            "tokens_used": 450,
        },
        {
            "case_id": "case-2",
            "case_name": "Invalid agency input",
            "input_data": {"domain": "agency.io"},
            "expected_output": {"tier": 3},
            "actual_output": {"tier": 2},
            "passed": False,
            "score": 0.0,
            "evaluator_name": "exact-match",
            "evaluator_type": "exact-match",
            "failure_reason": "Tier mismatch: got 2 expected 3",
            "latency_ms": 110,
            "tokens_used": 410,
        },
    ]

    record_resp = await async_client.post(
        f"/api/v1/evals/runs/{run_id}/results?duration_ms=230",
        json=results_payload,
    )
    assert record_resp.status_code == 200
    completed_run = record_resp.json()
    assert completed_run["status"] == "completed"
    assert completed_run["total_cases"] == 2
    assert completed_run["passed_cases"] == 1
    assert completed_run["failed_cases"] == 1
    assert completed_run["pass_rate"] == 0.5
    assert completed_run["duration_ms"] == 230
    assert len(completed_run["results"]) == 2

    # 4. Get run details
    get_run_resp = await async_client.get(f"/api/v1/evals/runs/{run_id}")
    assert get_run_resp.status_code == 200
    assert get_run_resp.json()["id"] == run_id
    assert len(get_run_resp.json()["results"]) == 2

    # 5. List runs
    list_runs_resp = await async_client.get(f"/api/v1/evals/runs?agent_id={agent.id}")
    assert list_runs_resp.status_code == 200
    assert list_runs_resp.json()["total"] == 1
    assert list_runs_resp.json()["runs"][0]["pass_rate"] == 0.5
