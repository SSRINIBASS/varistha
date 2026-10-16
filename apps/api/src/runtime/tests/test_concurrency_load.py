"""Concurrency and load test suite verifying 10+ concurrent agent stability."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any

import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from runtime.router import get_runtime
from shared.db.base import Base
from shared.db.session import get_db_session
from shared.telemetry import capture_run_spans, get_tracer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from runtime.mock import MockRuntime


@pytest.fixture
async def load_client(
    tmp_path: Path,
    mock_runtime: MockRuntime,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide a dedicated WAL-enabled file-backed test client for concurrent load tests."""
    db_file = tmp_path / "load_test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        connect_args={"timeout": 15},
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA busy_timeout=10000;"))

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_runtime] = lambda: mock_runtime

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


def _make_agent_spec(
    name: str,
    autonomy: str = "L1",
    outbound_enabled: bool = False,
) -> dict[str, Any]:
    """Generate a valid Agent Spec payload for concurrency tests."""
    plugins: list[dict[str, Any]] = [
        {"name": "web-fetch", "enabled": True},
    ]
    if outbound_enabled:
        plugins.append({"name": "email-send", "enabled": True})

    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "loadtest@example.com",
            "stage": "prototype",
            "version": "1.0.0",
        },
        "spec": {
            "role": f"Concurrency load test worker for {name}",
            "model": {
                "primary": "gpt-4o",
                "fallback": "ollama/llama3",
            },
            "instructions": "Execute assigned task under concurrent load.",
            "plugins": plugins,
            "autonomy": autonomy,
            "guardrails": {
                "input": ["injection-scan"],
                "output": ["schema-valid"],
            },
            "budget": {
                "max_usd_per_run": 1.00,
                "max_usd_per_day": 20.00,
            },
        },
    }


async def test_ten_concurrent_agents_independent_execution(load_client: AsyncClient) -> None:
    """10 distinct agents execute concurrently with full telemetry and zero race conditions."""
    agent_count = 10

    # 1. Register 10 distinct agents
    register_coros = [
        load_client.post("/api/v1/agents", json=_make_agent_spec(f"agent-concurrent-{i}"))
        for i in range(agent_count)
    ]
    register_responses = await asyncio.gather(*register_coros)
    for resp in register_responses:
        assert resp.status_code == 201
    agent_ids = [r.json()["id"] for r in register_responses]

    # 2. Trigger all 10 agents simultaneously
    trigger_coros = [
        load_client.post(
            f"/api/v1/agents/{agent_id}/runs",
            json={"input": {"task": f"load-benchmark-task-{i}"}},
        )
        for i, agent_id in enumerate(agent_ids)
    ]
    run_responses = await asyncio.gather(*trigger_coros)
    for resp in run_responses:
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["error"] is None

    run_ids = [r.json()["id"] for r in run_responses]
    assert len(set(run_ids)) == agent_count, "Each concurrent run must have a unique ID"

    # 3. Retrieve and inspect spans concurrently for all 10 runs
    span_coros = [load_client.get(f"/api/v1/runs/{run_id}/spans") for run_id in run_ids]
    span_responses = await asyncio.gather(*span_coros)

    for i, span_resp in enumerate(span_responses):
        assert span_resp.status_code == 200
        spans_data = span_resp.json()
        assert spans_data["total"] >= 2
        items = spans_data["items"]

        # Ensure all spans in this run match this run's ID
        for span in items:
            assert span["run_id"] == run_ids[i]

        # Verify root span belongs to the corresponding agent
        root_span = next(s for s in items if s["name"] == "agent.run")
        assert root_span["attributes"]["varistha.agent_name"] == f"agent-concurrent-{i}"
        assert root_span["status"] == "OK"


async def test_concurrent_approval_interrupts(
    load_client: AsyncClient,
    mock_runtime: MockRuntime,
) -> None:
    """10 concurrent agents requiring human approval enter waiting state cleanly."""
    agent_count = 10
    mock_runtime.waiting_approval = True

    try:
        # 1. Register 10 agents with outbound email plugin requiring approval
        reg_coros = [
            load_client.post(
                "/api/v1/agents",
                json=_make_agent_spec(f"agent-approval-{i}", autonomy="L1", outbound_enabled=True),
            )
            for i in range(agent_count)
        ]
        reg_resps = await asyncio.gather(*reg_coros)
        for resp in reg_resps:
            assert resp.status_code == 201
        agent_ids = [r.json()["id"] for r in reg_resps]

        # 2. Concurrently trigger outbound actions
        trigger_coros = [
            load_client.post(
                f"/api/v1/agents/{agent_id}/runs",
                json={
                    "input": {
                        "action": "email-send",
                        "recipient": f"lead-{i}@example.com",
                        "subject": f"Concurrent outreach {i}",
                    }
                },
            )
            for i, agent_id in enumerate(agent_ids)
        ]
        run_resps = await asyncio.gather(*trigger_coros)
        for resp in run_resps:
            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "waiting_approval"

        # 3. Verify 10 distinct approvals exist
        approvals_resp = await load_client.get("/api/v1/approvals?status=pending")
        assert approvals_resp.status_code == 200
        pending_approvals = approvals_resp.json().get("items", [])
        assert len(pending_approvals) >= agent_count

    finally:
        mock_runtime.waiting_approval = False


async def test_concurrent_span_isolation() -> None:
    """Trace buffers across concurrent tasks remain strictly isolated without crosstalk."""
    task_count = 15
    spans_per_task = 5

    async def _worker_task(task_id: int) -> tuple[str, list[str]]:
        run_uuid = uuid.uuid4()
        tracer = get_tracer("varistha.concurrency.test")

        with capture_run_spans(run_uuid) as buffer:
            for step in range(spans_per_task):
                span_name = f"task-{task_id}-step-{step}"
                with tracer.start_as_current_span(span_name):
                    await asyncio.sleep(0.002)

            captured_names = [s.name for s in buffer]
            return str(run_uuid), captured_names

    results = await asyncio.gather(*[_worker_task(i) for i in range(task_count)])

    assert len(results) == task_count
    for task_id, (_run_id, captured_names) in enumerate(results):
        assert len(captured_names) == spans_per_task
        expected_names = [f"task-{task_id}-step-{step}" for step in range(spans_per_task)]
        assert captured_names == expected_names, f"Crosstalk detected in task {task_id}"


async def test_high_concurrency_burst_stability(load_client: AsyncClient) -> None:
    """Execute a burst of 20 concurrent execution requests against a single agent."""
    # 1. Register agent
    reg = await load_client.post("/api/v1/agents", json=_make_agent_spec("agent-burst-target"))
    assert reg.status_code == 201
    agent_id = reg.json()["id"]

    # 2. Burst 20 requests in parallel
    burst_count = 20
    burst_coros = [
        load_client.post(
            f"/api/v1/agents/{agent_id}/runs",
            json={"input": {"task": f"burst-request-{i}"}},
        )
        for i in range(burst_count)
    ]
    burst_resps = await asyncio.gather(*burst_coros)

    success_count = sum(1 for r in burst_resps if r.status_code == 201)
    assert success_count == burst_count, f"Expected {burst_count} successes, got {success_count}"
