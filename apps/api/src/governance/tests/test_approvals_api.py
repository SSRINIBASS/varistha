"""Integration tests for Governance Approval REST API endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from governance.approvals.service import create_approval
from shared.db.models import Agent, AgentVersion, Run

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def seeded_run_and_approval(db_session: AsyncSession) -> tuple[Agent, Run, uuid.UUID]:
    """Seed an agent, run, and pending approval in the test database."""
    agent = Agent(
        id=uuid.uuid4(),
        name="email-campaign-agent",
        owner="growth@startup.io",
        stage="production",
        current_version="1.0.0",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent.id,
        version="1.0.0",
        spec={"spec": {"autonomy": "L1"}},
    )
    db_session.add(version)
    await db_session.flush()

    run = Run(
        id=uuid.uuid4(),
        agent_id=agent.id,
        agent_version_id=version.id,
        status="waiting_approval",
        trigger_type="api",
        input={"campaign": "q4_launch"},
    )
    db_session.add(run)
    await db_session.flush()

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="outbound_action",
        tool_name="send_newsletter",
        description="Broadcast newsletter to 5,000 subscribers",
        proposed_payload={
            "subject": "Exclusive Launch Offer!",
            "discount": "30%",
            "recipients_count": 5000,
        },
    )

    return agent, run, approval.id


@pytest.mark.asyncio
async def test_list_approvals_endpoint(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
):
    """GET /api/v1/approvals returns paginated list of approvals."""
    agent, run, approval_id = seeded_run_and_approval

    response = await async_client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(approval_id)
    assert data["items"][0]["status"] == "pending"
    assert data["items"][0]["tool_name"] == "send_newsletter"

    # Filter by agent_id
    res_agent = await async_client.get(f"/api/v1/approvals?agent_id={agent.id}")
    assert res_agent.status_code == 200
    assert res_agent.json()["total"] == 1

    # Filter by run_id
    res_run = await async_client.get(f"/api/v1/approvals?run_id={run.id}")
    assert res_run.status_code == 200
    assert res_run.json()["total"] == 1

    # Filter by unknown status
    res_rejected = await async_client.get("/api/v1/approvals?status=rejected")
    assert res_rejected.status_code == 200
    assert res_rejected.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_approval_by_id(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
):
    """GET /api/v1/approvals/{id} returns approval detail or 404."""
    _, _, approval_id = seeded_run_and_approval

    response = await async_client.get(f"/api/v1/approvals/{approval_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(approval_id)
    assert data["status"] == "pending"
    assert data["proposed_payload"]["discount"] == "30%"

    # Non-existent ID returns 404
    missing_id = uuid.uuid4()
    not_found_res = await async_client.get(f"/api/v1/approvals/{missing_id}")
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_resolve_approval_endpoint_approve(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
    db_session: AsyncSession,
):
    """POST /api/v1/approvals/{id}/resolve with 'approve' marks approval approved."""
    _, run, approval_id = seeded_run_and_approval

    resolve_payload = {
        "decision": "approve",
        "reviewer": "operator@startup.io",
        "feedback": "Approved for general broadcast",
    }
    response = await async_client.post(
        f"/api/v1/approvals/{approval_id}/resolve",
        json=resolve_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["reviewer"] == "operator@startup.io"
    assert data["approved_payload"]["discount"] == "30%"

    # Check that associated run moved from waiting_approval to completed
    await db_session.refresh(run)
    assert run.status == "completed"
    assert run.output is not None
    assert run.output["approved_by"] == "operator@startup.io"


@pytest.mark.asyncio
async def test_resolve_approval_endpoint_reject(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
    db_session: AsyncSession,
):
    """POST /api/v1/approvals/{id}/resolve with 'reject' marks approval rejected and fails run."""
    _, run, approval_id = seeded_run_and_approval

    resolve_payload = {
        "decision": "reject",
        "reviewer": "security@startup.io",
        "feedback": "Discount too high, policy violation",
    }
    response = await async_client.post(
        f"/api/v1/approvals/{approval_id}/resolve",
        json=resolve_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["approved_payload"] is None

    # Check that associated run failed
    await db_session.refresh(run)
    assert run.status == "failed"
    assert run.error is not None
    assert "Discount too high" in run.error


@pytest.mark.asyncio
async def test_resolve_approval_endpoint_edit(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
    db_session: AsyncSession,
):
    """POST /api/v1/approvals/{id}/resolve with 'edit' computes payload diff and completes run."""
    _, run, approval_id = seeded_run_and_approval

    edited_payload = {
        "subject": "Exclusive Launch Offer!",
        "discount": "15%",  # Changed from 30%
        "recipients_count": 5000,
        "operator_tag": "approved_q4",  # Added
    }
    resolve_payload = {
        "decision": "edit",
        "reviewer": "growth_lead@startup.io",
        "approved_payload": edited_payload,
        "feedback": "Capped discount at 15%",
    }
    response = await async_client.post(
        f"/api/v1/approvals/{approval_id}/resolve",
        json=resolve_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "edited"
    assert data["approved_payload"] == edited_payload
    assert data["diff"] is not None
    assert data["diff"]["modified"]["discount"] == {"old": "30%", "new": "15%"}
    assert data["diff"]["added"]["operator_tag"] == "approved_q4"

    # Check that associated run completed with edited payload
    await db_session.refresh(run)
    assert run.status == "completed"
    assert run.output is not None
    assert run.output["payload"]["discount"] == "15%"


@pytest.mark.asyncio
async def test_resolve_already_resolved_conflict(
    async_client: AsyncClient,
    seeded_run_and_approval: tuple[Agent, Run, uuid.UUID],
):
    """Resolving an already resolved approval returns 409 Conflict."""
    _, _, approval_id = seeded_run_and_approval

    resolve_payload = {
        "decision": "approve",
        "reviewer": "lead@startup.io",
    }
    res1 = await async_client.post(
        f"/api/v1/approvals/{approval_id}/resolve",
        json=resolve_payload,
    )
    assert res1.status_code == 200

    res2 = await async_client.post(
        f"/api/v1/approvals/{approval_id}/resolve",
        json=resolve_payload,
    )
    assert res2.status_code == 409
