"""Unit tests for approval service logic and payload diff computation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from governance.approvals.service import (
    ApprovalAlreadyResolvedError,
    ApprovalNotFoundError,
    compute_payload_diff,
    create_approval,
    get_approval,
    list_approvals,
    resolve_approval,
)
from shared.db.models import Agent, AgentVersion, Run

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def test_compute_payload_diff_identical():
    """Identical payloads produce an empty diff."""
    proposed = {"to": "user@example.com", "subject": "Hello", "body": "World"}
    approved = {"to": "user@example.com", "subject": "Hello", "body": "World"}

    diff = compute_payload_diff(proposed, approved)
    assert diff == {"added": {}, "removed": {}, "modified": {}}


def test_compute_payload_diff_add_remove_modify():
    """Diff correctly isolates added, removed, and modified attributes."""
    proposed = {
        "to": "user@example.com",
        "subject": "Discount offer",
        "discount_percent": 20,
        "internal_note": "Confidential",
    }
    approved = {
        "to": "user@example.com",
        "subject": "Special VIP Offer",  # modified
        "discount_percent": 10,  # modified
        "send_at": "2026-10-16T10:00:00Z",  # added
        # internal_note removed
    }

    diff = compute_payload_diff(proposed, approved)
    assert diff["added"] == {"send_at": "2026-10-16T10:00:00Z"}
    assert diff["removed"] == {"internal_note": "Confidential"}
    assert diff["modified"] == {
        "subject": {"old": "Discount offer", "new": "Special VIP Offer"},
        "discount_percent": {"old": 20, "new": 10},
    }


def test_compute_payload_diff_nested():
    """Nested dictionaries are recursively diffed."""
    proposed = {
        "recipient": {"name": "Alice", "role": "Junior"},
        "budget": {"amount": 500, "currency": "USD"},
    }
    approved = {
        "recipient": {"name": "Alice", "role": "Senior"},
        "budget": {"amount": 250, "currency": "USD"},
    }

    diff = compute_payload_diff(proposed, approved)
    assert diff["added"] == {}
    assert diff["removed"] == {}
    assert "recipient" in diff["modified"]
    assert diff["modified"]["recipient"]["modified"] == {"role": {"old": "Junior", "new": "Senior"}}
    assert diff["modified"]["budget"]["modified"] == {"amount": {"old": 500, "new": 250}}


@pytest.fixture
async def setup_agent_and_run(db_session: AsyncSession) -> tuple[Agent, Run]:
    """Set up an agent and a run in the test database."""
    agent = Agent(
        id=uuid.uuid4(),
        name="sales-outreach-agent",
        owner="srinibass@startup.io",
        current_version="0.1.0",
        stage="staging",
    )
    db_session.add(agent)
    await db_session.flush()

    version = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent.id,
        version="0.1.0",
        spec={"spec": {"autonomy": "L1"}},
    )
    db_session.add(version)
    await db_session.flush()

    run = Run(
        id=uuid.uuid4(),
        agent_id=agent.id,
        agent_version_id=version.id,
        status="waiting_approval",
        trigger_type="manual",
        input={"lead_id": "123"},
    )
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(agent)
    await db_session.refresh(run)
    return agent, run


@pytest.mark.asyncio
async def test_create_and_get_approval(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Creating an approval persists it in 'pending' status."""
    agent, run = setup_agent_and_run

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="outbound_action",
        tool_name="send_email",
        description="Send introductory email to high-value lead",
        proposed_payload={"to": "lead@company.com", "subject": "Intro"},
    )

    assert approval.id is not None
    assert approval.status == "pending"
    assert approval.tool_name == "send_email"
    assert approval.proposed_payload == {"to": "lead@company.com", "subject": "Intro"}
    assert approval.approved_payload is None
    assert approval.resolved_at is None

    fetched = await get_approval(db_session, approval.id)
    assert fetched is not None
    assert fetched.id == approval.id
    assert fetched.agent_id == agent.id


@pytest.mark.asyncio
async def test_resolve_approval_approve(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Approving without changes sets status='approved' and copies proposed payload."""
    agent, run = setup_agent_and_run

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="tool_call",
        tool_name="crm_write",
        proposed_payload={"stage": "contacted", "deal_value": 10000},
    )

    resolved = await resolve_approval(
        session=db_session,
        approval_id=approval.id,
        decision="approve",
        reviewer="srinibass@company.com",
        feedback="Looks good to send",
    )

    assert resolved.status == "approved"
    assert resolved.approved_payload == {"stage": "contacted", "deal_value": 10000}
    assert resolved.diff is None
    assert resolved.reviewer == "srinibass@company.com"
    assert resolved.feedback == "Looks good to send"
    assert resolved.resolved_at is not None


@pytest.mark.asyncio
async def test_resolve_approval_reject(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Rejecting an approval marks it 'rejected' with reviewer and feedback."""
    agent, run = setup_agent_and_run

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="outbound_action",
        proposed_payload={"post": "Unverified announcement"},
    )

    resolved = await resolve_approval(
        session=db_session,
        approval_id=approval.id,
        decision="reject",
        reviewer="security-lead",
        feedback="Not authorized for public disclosure yet",
    )

    assert resolved.status == "rejected"
    assert resolved.approved_payload is None
    assert resolved.reviewer == "security-lead"
    assert resolved.feedback == "Not authorized for public disclosure yet"
    assert resolved.resolved_at is not None


@pytest.mark.asyncio
async def test_resolve_approval_edit(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Editing proposed action computes diff, sets approved payload, and status='edited'."""
    agent, run = setup_agent_and_run

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="outbound_action",
        proposed_payload={"recipient": "ceo@startup.io", "body": "Hey there! 50% discount."},
    )

    edited_payload = {"recipient": "ceo@startup.io", "body": "Hello. 20% discount offer."}
    resolved = await resolve_approval(
        session=db_session,
        approval_id=approval.id,
        decision="edit",
        reviewer="manager@startup.io",
        approved_payload=edited_payload,
        feedback="Reduced discount from 50% to 20% and improved tone.",
    )

    assert resolved.status == "edited"
    assert resolved.approved_payload == edited_payload
    assert resolved.diff is not None
    assert resolved.diff["modified"]["body"] == {
        "old": "Hey there! 50% discount.",
        "new": "Hello. 20% discount offer.",
    }
    assert resolved.reviewer == "manager@startup.io"


@pytest.mark.asyncio
async def test_resolve_approval_already_resolved(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Attempting to resolve an already resolved approval raises an error."""
    agent, run = setup_agent_and_run

    approval = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="outbound_action",
        proposed_payload={"text": "Hello"},
    )

    await resolve_approval(
        session=db_session,
        approval_id=approval.id,
        decision="approve",
        reviewer="admin",
    )

    with pytest.raises(ApprovalAlreadyResolvedError):
        await resolve_approval(
            session=db_session,
            approval_id=approval.id,
            decision="reject",
            reviewer="admin2",
        )


@pytest.mark.asyncio
async def test_resolve_approval_not_found(db_session: AsyncSession):
    """Resolving a non-existent approval raises ApprovalNotFoundError."""
    with pytest.raises(ApprovalNotFoundError):
        await resolve_approval(
            session=db_session,
            approval_id=uuid.uuid4(),
            decision="approve",
            reviewer="admin",
        )


@pytest.mark.asyncio
async def test_list_approvals_filtering(
    db_session: AsyncSession, setup_agent_and_run: tuple[Agent, Run]
):
    """Filtering approvals by status, agent_id, and run_id works with pagination."""
    agent, run = setup_agent_and_run

    appr1 = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="tool_call",
        proposed_payload={"cmd": "1"},
    )
    appr2 = await create_approval(
        session=db_session,
        run_id=run.id,
        agent_id=agent.id,
        action_type="tool_call",
        proposed_payload={"cmd": "2"},
    )
    await resolve_approval(
        session=db_session,
        approval_id=appr1.id,
        decision="approve",
        reviewer="admin",
    )

    # Filter pending
    pending_items, total_pending = await list_approvals(db_session, status="pending")
    assert total_pending == 1
    assert pending_items[0].id == appr2.id

    # Filter approved
    approved_items, total_approved = await list_approvals(db_session, status="approved")
    assert total_approved == 1
    assert approved_items[0].id == appr1.id

    # Filter by agent_id
    agent_items, total_agent = await list_approvals(db_session, agent_id=agent.id)
    assert total_agent == 2
    assert len(agent_items) == 2
