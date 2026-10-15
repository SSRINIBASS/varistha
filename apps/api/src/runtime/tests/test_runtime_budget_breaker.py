"""Integration tests for runtime budget tracking, rate limits, and kill switch circuit breakers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from runtime.interface import RunContext, RunResult
from runtime.service import (
    BudgetExceededError,
    KillSwitchTrippedError,
    trigger_agent_run,
)
from shared.db.models import Agent, AgentVersion, Run, SystemSetting

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class MockRuntimeWithCost:
    """Mock runtime returning customizable cost and status."""

    def __init__(
        self,
        cost_usd: float = 0.05,
        status: str = "completed",
        error: str | None = None,
    ) -> None:
        """Initialize mock runtime with cost and outcome."""
        self.cost_usd = cost_usd
        self.status = status
        self.error = error

    async def execute(self, context: RunContext) -> RunResult:
        """Simulate execution evaluating per-run budget ceiling."""
        spec_body = context.spec_snapshot.get("spec", {})
        budget = spec_body.get("budget", {})
        max_usd_per_run = budget.get("max_usd_per_run")
        if max_usd_per_run is not None and max_usd_per_run > 0 and self.cost_usd > max_usd_per_run:
            err_msg = (
                f"budget_exceeded: Run cost of ${self.cost_usd:.4f} "
                f"exceeded maximum per-run budget of ${max_usd_per_run:.2f}"
            )
            return RunResult(
                status="failed",
                output={},
                cost_usd=self.cost_usd,
                total_tokens=1000,
                error=err_msg,
            )

        return RunResult(
            status=self.status,
            output={"result": "success"},
            cost_usd=self.cost_usd,
            total_tokens=250,
            error=self.error,
        )


@pytest.fixture
async def agent_with_budget(db_session: AsyncSession) -> Agent:
    """Seed an agent with specific per-run and per-day budgets."""
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        name=f"budgeted-agent-{uuid.uuid4().hex[:6]}",
        owner="ops@example.com",
        stage="production",
        current_version="1.0.0",
        is_active=True,
        kill_switch_tripped=False,
    )
    db_session.add(agent)

    spec: dict[str, Any] = {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": agent.name,
            "owner": "ops@example.com",
            "version": "1.0.0",
            "stage": "production",
        },
        "spec": {
            "role": "Lead Researcher",
            "autonomy": "L2",
            "model": {"primary": "gpt-4o"},
            "budget": {
                "max_usd_per_run": 0.50,
                "max_usd_per_day": 5.00,
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


async def test_trigger_agent_run_blocked_when_agent_kill_switch_tripped(
    db_session: AsyncSession,
    agent_with_budget: Agent,
) -> None:
    """Pre-flight check halts run when agent kill switch is tripped."""
    agent_with_budget.kill_switch_tripped = True
    agent_with_budget.kill_switch_reason = "Malfunctioning scraper"
    agent_with_budget.is_active = False
    await db_session.commit()

    runtime = MockRuntimeWithCost(cost_usd=0.01)

    with pytest.raises(KillSwitchTrippedError) as exc_info:
        await trigger_agent_run(
            session=db_session,
            id_or_name=agent_with_budget.name,
            input_data={"prompt": "test"},
            trigger_type="manual",
            runtime=runtime,  # type: ignore[arg-type]
        )

    assert "kill_switch_tripped" in str(exc_info.value)
    assert "Malfunctioning scraper" in str(exc_info.value)


async def test_trigger_agent_run_blocked_when_global_emergency_stop_active(
    db_session: AsyncSession,
    agent_with_budget: Agent,
) -> None:
    """Pre-flight check halts run when system-wide emergency stop is enabled."""
    setting = SystemSetting(
        key="global_kill_switch",
        value={"enabled": True, "reason": "DDoS Mitigation in progress"},
        updated_at=datetime.now(UTC),
    )
    db_session.add(setting)
    await db_session.commit()

    runtime = MockRuntimeWithCost(cost_usd=0.01)

    with pytest.raises(KillSwitchTrippedError) as exc_info:
        await trigger_agent_run(
            session=db_session,
            id_or_name=agent_with_budget.name,
            input_data={"prompt": "test"},
            trigger_type="manual",
            runtime=runtime,  # type: ignore[arg-type]
        )

    assert "kill_switch_tripped: Global emergency stop is active" in str(exc_info.value)


async def test_trigger_agent_run_blocked_when_daily_budget_exhausted(
    db_session: AsyncSession,
    agent_with_budget: Agent,
) -> None:
    """Pre-flight check halts run when accumulated daily spend reaches max_usd_per_day."""
    # Seed an earlier run today that consumed the entire $5.00 daily budget
    prior_run = Run(
        id=uuid.uuid4(),
        agent_id=agent_with_budget.id,
        status="completed",
        trigger_type="manual",
        cost_usd=5.00,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    db_session.add(prior_run)
    await db_session.commit()

    runtime = MockRuntimeWithCost(cost_usd=0.01)

    with pytest.raises(BudgetExceededError) as exc_info:
        await trigger_agent_run(
            session=db_session,
            id_or_name=agent_with_budget.name,
            input_data={"prompt": "test"},
            trigger_type="manual",
            runtime=runtime,  # type: ignore[arg-type]
        )

    assert "budget_exceeded: Daily budget limit of $5.00 reached" in str(exc_info.value)


async def test_trigger_agent_run_aborted_when_single_run_cost_exceeds_max_usd_per_run(
    db_session: AsyncSession,
    agent_with_budget: Agent,
) -> None:
    """A runaway single execution exceeding max_usd_per_run ($0.50) is marked failed."""
    # Mock a run that cost $0.75, which exceeds the $0.50 per-run ceiling
    runtime = MockRuntimeWithCost(cost_usd=0.75)

    run = await trigger_agent_run(
        session=db_session,
        id_or_name=agent_with_budget.name,
        input_data={"prompt": "long recursive query"},
        trigger_type="manual",
        runtime=runtime,  # type: ignore[arg-type]
    )

    assert run.status == "failed"
    assert run.cost_usd == 0.75
    expected_msg = "budget_exceeded: Run cost of $0.7500 exceeded maximum per-run budget of $0.50"
    assert expected_msg in (run.error or "")

    # Check root span attributes in database
    await db_session.refresh(run)
    spans = run.spans
    assert len(spans) > 0
    root_span = spans[0]
    attrs = root_span.attributes or {}
    assert attrs.get("varistha.budget.exceeded") is True
