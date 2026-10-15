"""Integration tests for budget monitoring and kill switch REST endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shared.db.models import Agent, AgentVersion

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


async def _seed_agent_with_budget(db_session: AsyncSession) -> Agent:
    """Seed a test agent with active version and budget configuration."""
    agent = Agent(
        id=uuid.uuid4(),
        name=f"market-scanner-{uuid.uuid4().hex[:6]}",
        owner="ops@example.com",
        stage="staging",
        current_version="1.0.0",
        is_active=True,
        kill_switch_tripped=False,
    )
    db_session.add(agent)

    spec = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {"name": agent.name, "owner": "ops@example.com", "version": "1.0.0"},
        "spec": {
            "role": "Scanner",
            "model": {"primary": "gpt-4o"},
            "budget": {
                "max_usd_per_run": 1.00,
                "max_usd_per_day": 20.00,
            },
        },
    }
    ver = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent.id,
        version="1.0.0",
        spec=spec,
    )
    db_session.add(ver)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


async def test_get_agent_budget_api(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/agents/{id_or_name}/budget returns budget status."""
    agent = await _seed_agent_with_budget(db_session)

    resp = await async_client.get(f"/api/v1/agents/{agent.name}/budget")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == str(agent.id)
    assert data["agent_name"] == agent.name
    assert data["max_usd_per_run"] == 1.00
    assert data["max_usd_per_day"] == 20.00
    assert data["is_active"] is True
    assert data["kill_switch_tripped"] is False


async def test_get_agent_budget_not_found(async_client: AsyncClient) -> None:
    """GET /api/v1/agents/{nonexistent}/budget returns 404."""
    resp = await async_client.get("/api/v1/agents/nonexistent-agent/budget")
    assert resp.status_code == 404


async def test_trip_and_resume_agent_kill_switch_api(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST /kill trips the switch and POST /resume reactivates the agent."""
    agent = await _seed_agent_with_budget(db_session)

    # 1. Kill
    kill_payload = {
        "reason": "Exceeded token threshold",
        "operator": "security_team",
    }
    kill_resp = await async_client.post(
        f"/api/v1/agents/{agent.id}/kill",
        json=kill_payload,
    )
    assert kill_resp.status_code == 200
    kill_data = kill_resp.json()
    assert kill_data["kill_switch_tripped"] is True
    assert kill_data["is_active"] is False
    assert "[security_team] Exceeded token threshold" in kill_data["reason"]

    # Verify budget status reflects kill
    budget_resp = await async_client.get(f"/api/v1/agents/{agent.id}/budget")
    assert budget_resp.status_code == 200
    assert budget_resp.json()["kill_switch_tripped"] is True

    # 2. Resume
    resume_resp = await async_client.post(
        f"/api/v1/agents/{agent.id}/resume?operator=supervisor",
    )
    assert resume_resp.status_code == 200
    resume_data = resume_resp.json()
    assert resume_data["kill_switch_tripped"] is False
    assert resume_data["is_active"] is True
    assert resume_data["reason"] is None


async def test_global_kill_switch_api(async_client: AsyncClient) -> None:
    """GET and POST /api/v1/system/kill-switch inspect and toggle global stop."""
    # Check initial
    get_resp = await async_client.get("/api/v1/system/kill-switch")
    assert get_resp.status_code == 200
    assert get_resp.json()["enabled"] is False

    # Enable
    post_resp = await async_client.post(
        "/api/v1/system/kill-switch",
        json={"enabled": True, "reason": "Global security lockdown", "operator": "ciso"},
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["enabled"] is True
    assert data["reason"] == "Global security lockdown"
    assert data["operator"] == "ciso"
    assert data["tripped_at"] is not None

    # Check updated status
    get_resp2 = await async_client.get("/api/v1/system/kill-switch")
    assert get_resp2.status_code == 200
    assert get_resp2.json()["enabled"] is True

    # Disable
    post_resp2 = await async_client.post(
        "/api/v1/system/kill-switch",
        json={"enabled": False},
    )
    assert post_resp2.status_code == 200
    assert post_resp2.json()["enabled"] is False
