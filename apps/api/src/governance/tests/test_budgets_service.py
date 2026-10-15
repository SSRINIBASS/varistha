"""Unit tests for budget tracking and kill switch domain service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from governance.budgets.service import (
    check_post_run_budget_breaker,
    check_pre_flight_budget_and_kill_switch,
    get_agent_budget_status,
    get_daily_spend,
    get_global_kill_switch,
    resume_agent,
    set_global_kill_switch,
    trip_agent_kill_switch,
)
from shared.db.models import Agent, AgentVersion, Run

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def sample_agent_with_budget(db_session: AsyncSession) -> Agent:
    """Create an agent with an active version specifying budgets."""
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        name=f"finance-bot-{uuid.uuid4().hex[:6]}",
        owner="finance@example.com",
        stage="production",
        current_version="1.0.0",
        is_active=True,
        kill_switch_tripped=False,
    )
    db_session.add(agent)

    spec = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": agent.name,
            "owner": "finance@example.com",
            "version": "1.0.0",
            "stage": "production",
        },
        "spec": {
            "role": "Financial Assistant",
            "instructions": "Be accurate with numbers.",
            "autonomy": "L2",
            "model": {"primary": "gpt-4o"},
            "budget": {
                "max_usd_per_run": 0.50,
                "max_usd_per_day": 10.00,
            },
        },
    }
    version = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent.id,
        version="1.0.0",
        spec=spec,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


async def test_get_daily_spend_and_runs_count(
    db_session: AsyncSession,
    sample_agent_with_budget: Agent,
) -> None:
    """Verify daily spend correctly aggregates runs within the time window."""
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=2)

    # 1. Run yesterday (should be excluded by default start of day)
    run_old = Run(
        id=uuid.uuid4(),
        agent_id=sample_agent_with_budget.id,
        status="completed",
        trigger_type="schedule",
        cost_usd=5.00,
        started_at=yesterday,
        completed_at=yesterday,
    )
    # 2. Runs today
    run_today1 = Run(
        id=uuid.uuid4(),
        agent_id=sample_agent_with_budget.id,
        status="completed",
        trigger_type="manual",
        cost_usd=2.50,
        started_at=now,
        completed_at=now,
    )
    run_today2 = Run(
        id=uuid.uuid4(),
        agent_id=sample_agent_with_budget.id,
        status="completed",
        trigger_type="manual",
        cost_usd=1.25,
        started_at=now,
        completed_at=now,
    )
    db_session.add_all([run_old, run_today1, run_today2])
    await db_session.commit()

    spend, count = await get_daily_spend(db_session, sample_agent_with_budget.id)
    assert spend == 3.75
    assert count == 2


async def test_get_agent_budget_status(
    db_session: AsyncSession,
    sample_agent_with_budget: Agent,
) -> None:
    """Verify full budget status calculations including remaining and utilization."""
    now = datetime.now(UTC)
    run = Run(
        id=uuid.uuid4(),
        agent_id=sample_agent_with_budget.id,
        status="completed",
        trigger_type="manual",
        cost_usd=2.00,
        started_at=now,
        completed_at=now,
    )
    db_session.add(run)
    await db_session.commit()

    status = await get_agent_budget_status(db_session, sample_agent_with_budget)
    assert status.agent_id == sample_agent_with_budget.id
    assert status.is_active is True
    assert status.kill_switch_tripped is False
    assert status.max_usd_per_run == 0.50
    assert status.max_usd_per_day == 10.00
    assert status.daily_spend_usd == 2.00
    assert status.daily_runs_count == 1
    assert status.daily_budget_remaining_usd == 8.00
    assert status.daily_budget_utilization_pct == 20.00


async def test_trip_and_resume_agent_kill_switch(
    db_session: AsyncSession,
    sample_agent_with_budget: Agent,
) -> None:
    """Trip an agent kill switch and then resume it."""
    # Trip
    halted = await trip_agent_kill_switch(
        db_session,
        sample_agent_with_budget,
        reason="Abnormal token consumption",
        operator="alice",
    )
    assert halted.kill_switch_tripped is True
    assert halted.is_active is False
    assert halted.kill_switch_reason == "[alice] Abnormal token consumption"
    assert halted.kill_switch_tripped_at is not None

    # Resume
    resumed = await resume_agent(
        db_session,
        halted,
        operator="alice",
    )
    assert resumed.kill_switch_tripped is False
    assert resumed.is_active is True
    assert resumed.kill_switch_reason is None
    assert resumed.kill_switch_tripped_at is None


async def test_global_kill_switch_toggle(db_session: AsyncSession) -> None:
    """Check setting and querying the global emergency stop."""
    initial = await get_global_kill_switch(db_session)
    assert initial.enabled is False

    enabled_status = await set_global_kill_switch(
        db_session,
        enabled=True,
        reason="Security audit in progress",
        operator="admin",
    )
    assert enabled_status.enabled is True
    assert enabled_status.reason == "Security audit in progress"
    assert enabled_status.operator == "admin"
    assert enabled_status.tripped_at is not None

    current = await get_global_kill_switch(db_session)
    assert current.enabled is True

    # Disable
    disabled_status = await set_global_kill_switch(
        db_session,
        enabled=False,
        reason=None,
        operator="admin",
    )
    assert disabled_status.enabled is False


async def test_check_pre_flight_budget_and_kill_switch(
    db_session: AsyncSession,
    sample_agent_with_budget: Agent,
) -> None:
    """Test all pre-flight barrier conditions."""
    spec = {
        "spec": {
            "budget": {
                "max_usd_per_day": 5.00,
            }
        }
    }

    # 1. Normal state -> allowed
    allowed, reason = await check_pre_flight_budget_and_kill_switch(
        db_session, sample_agent_with_budget, spec
    )
    assert allowed is True
    assert reason is None

    # 2. Agent kill switch tripped -> blocked
    sample_agent_with_budget.kill_switch_tripped = True
    sample_agent_with_budget.kill_switch_reason = "Manual halt"
    allowed, reason = await check_pre_flight_budget_and_kill_switch(
        db_session, sample_agent_with_budget, spec
    )
    assert allowed is False
    assert "kill_switch_tripped" in (reason or "")

    # Reset agent
    sample_agent_with_budget.kill_switch_tripped = False
    sample_agent_with_budget.kill_switch_reason = None

    # 3. Global emergency stop -> blocked
    await set_global_kill_switch(db_session, enabled=True, reason="Infra migration")
    allowed, reason = await check_pre_flight_budget_and_kill_switch(
        db_session, sample_agent_with_budget, spec
    )
    assert allowed is False
    assert "Global emergency stop is active" in (reason or "")

    # Reset global
    await set_global_kill_switch(db_session, enabled=False)

    # 4. Daily budget limit reached -> blocked
    run = Run(
        id=uuid.uuid4(),
        agent_id=sample_agent_with_budget.id,
        status="completed",
        trigger_type="manual",
        cost_usd=5.50,
        started_at=datetime.now(UTC),
    )
    db_session.add(run)
    await db_session.commit()

    allowed, reason = await check_pre_flight_budget_and_kill_switch(
        db_session, sample_agent_with_budget, spec
    )
    assert allowed is False
    assert "budget_exceeded" in (reason or "")
    assert "Daily budget limit of $5.00 reached" in (reason or "")


def test_check_post_run_budget_breaker() -> None:
    """Verify per-run budget ceiling violation checks."""
    spec = {
        "spec": {
            "budget": {
                "max_usd_per_run": 0.50,
            }
        }
    }

    # Within limit
    allowed, reason = check_post_run_budget_breaker(0.49, spec)
    assert allowed is True
    assert reason is None

    # Exact limit
    allowed, reason = check_post_run_budget_breaker(0.50, spec)
    assert allowed is True
    assert reason is None

    # Exceeded
    allowed, reason = check_post_run_budget_breaker(0.51, spec)
    assert allowed is False
    assert reason is not None
    assert "budget_exceeded: Run cost of $0.5100 exceeded maximum per-run budget of $0.50" in reason
