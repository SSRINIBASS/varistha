"""Integration tests for agent lifecycle stage promotions and audit history."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import pytest
from shared.db.models import Run

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def valid_agent_spec(
    name: str = "promotion-agent",
    stage: str = "draft",
    guardrails: dict[str, Any] | None = None,
    budget: dict[str, Any] | None = None,
    evals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a valid AgentSpec dict for testing."""
    spec_data: dict[str, Any] = {
        "role": "Autonomous research agent",
        "model": {"primary": "gpt-4o"},
        "instructions": "Research leads systematically.",
        "autonomy": "L1",
        "triggers": [{"type": "manual"}],
    }
    if guardrails is not None:
        spec_data["guardrails"] = guardrails
    if budget is not None:
        spec_data["budget"] = budget
    if evals is not None:
        spec_data["evals"] = evals

    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "founder@example.com",
            "stage": stage,
            "version": "0.1.0",
        },
        "spec": spec_data,
    }


@pytest.mark.asyncio
async def test_preview_gates_dry_run(async_client: AsyncClient) -> None:
    """Preview gates endpoint returns checklist without altering agent state."""
    spec = valid_agent_spec(name="preview-agent", stage="draft")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201
    agent_id = reg_resp.json()["id"]

    # Preview promotion to prototype (fails because 0 runs)
    prev_resp = await async_client.get(f"/api/v1/agents/{agent_id}/gates/prototype")
    assert prev_resp.status_code == 200
    prev_data = prev_resp.json()
    assert prev_data["allowed"] is False
    assert prev_data["from_stage"] == "draft"
    assert prev_data["to_stage"] == "prototype"
    assert any(c["name"] == "successful_run" and not c["passed"] for c in prev_data["checks"])

    # Verify agent stage did NOT change
    agent_resp = await async_client.get(f"/api/v1/agents/{agent_id}")
    assert agent_resp.json()["stage"] == "draft"


@pytest.mark.asyncio
async def test_promote_draft_to_prototype_blocked_without_run(async_client: AsyncClient) -> None:
    """Draft -> Prototype is blocked if agent has not run successfully."""
    spec = valid_agent_spec(name="draft-agent", stage="draft")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201

    promote_resp = await async_client.post(
        "/api/v1/agents/draft-agent/promote",
        json={
            "to_stage": "prototype",
            "promoted_by": "lead-engineer@example.com",
            "reason": "Ready for initial prototyping",
        },
    )
    assert promote_resp.status_code == 422
    err_data = promote_resp.json()["detail"]
    assert "evaluation" in err_data
    assert err_data["evaluation"]["allowed"] is False


@pytest.mark.asyncio
async def test_promote_draft_to_prototype_success(
    async_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Draft -> Prototype succeeds when at least one run was successful."""
    spec = valid_agent_spec(name="proto-candidate", stage="draft")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201
    agent_id = reg_resp.json()["id"]

    # Directly record a completed execution run in the database
    async with session_factory() as session:
        run = Run(
            agent_id=uuid.UUID(agent_id),
            status="completed",
            trigger_type="manual",
            input={"query": "tech companies"},
            output={"result": "found 10 leads"},
        )
        session.add(run)
        await session.commit()

    # Now promote
    promote_resp = await async_client.post(
        f"/api/v1/agents/{agent_id}/promote",
        json={
            "to_stage": "prototype",
            "promoted_by": "qa@example.com",
            "reason": "Verified initial execution run",
        },
    )
    assert promote_resp.status_code == 200
    data = promote_resp.json()
    assert data["agent"]["stage"] == "prototype"
    assert data["transition"]["from_stage"] == "draft"
    assert data["transition"]["to_stage"] == "prototype"
    assert data["transition"]["promoted_by"] == "qa@example.com"
    assert data["evaluation"]["allowed"] is True

    # Verify audit history
    hist_resp = await async_client.get(f"/api/v1/agents/{agent_id}/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 1
    assert history[0]["from_stage"] == "draft"
    assert history[0]["to_stage"] == "prototype"
    assert history[0]["promoted_by"] == "qa@example.com"


@pytest.mark.asyncio
async def test_rollback_requires_reason(
    async_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Demotion/rollback from prototype to draft requires an explanatory reason."""
    spec = valid_agent_spec(name="rollback-agent", stage="draft")
    reg_resp = await async_client.post("/api/v1/agents", json=spec)
    assert reg_resp.status_code == 201
    agent_id = reg_resp.json()["id"]

    # Directly record a completed run and promote to prototype
    async with session_factory() as session:
        run = Run(
            agent_id=uuid.UUID(agent_id),
            status="completed",
            trigger_type="manual",
        )
        session.add(run)
        await session.commit()

    await async_client.post(
        "/api/v1/agents/rollback-agent/promote",
        json={"to_stage": "prototype", "promoted_by": "admin@example.com"},
    )

    # Rollback without reason -> blocked
    rb_fail = await async_client.post(
        "/api/v1/agents/rollback-agent/promote",
        json={"to_stage": "draft", "promoted_by": "admin@example.com"},
    )
    assert rb_fail.status_code == 422

    # Rollback with reason -> succeeds
    rb_ok = await async_client.post(
        "/api/v1/agents/rollback-agent/promote",
        json={
            "to_stage": "draft",
            "promoted_by": "admin@example.com",
            "reason": "Spec redesign needed before re-evaluating",
        },
    )
    assert rb_ok.status_code == 200
    assert rb_ok.json()["agent"]["stage"] == "draft"
    assert rb_ok.json()["transition"]["reason"] == "Spec redesign needed before re-evaluating"

    # History shows 2 transitions now
    hist_resp = await async_client.get("/api/v1/agents/rollback-agent/history")
    assert len(hist_resp.json()) == 2
