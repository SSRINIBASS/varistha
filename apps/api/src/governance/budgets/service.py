"""Domain service for budget tracking, spend monitoring, and kill switch circuit breakers."""

from __future__ import annotations

import uuid  # noqa: TC003
from datetime import UTC, datetime, time
from typing import TYPE_CHECKING, Any

from governance.budgets.schemas import (
    AgentBudgetStatusResponse,
    GlobalKillSwitchStatus,
)
from shared.db.models import Agent, AgentVersion, Run, SystemSetting
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

GLOBAL_KILL_SWITCH_KEY = "global_kill_switch"


def get_start_of_current_day_utc() -> datetime:
    """Return midnight UTC for the current calendar date."""
    now = datetime.now(UTC)
    return datetime.combine(now.date(), time.min, tzinfo=UTC)


async def get_daily_spend(
    session: AsyncSession,
    agent_id: uuid.UUID,
    since: datetime | None = None,
) -> tuple[float, int]:
    """Calculate total USD spend and completed run count for an agent since a given timestamp."""
    if since is None:
        since = get_start_of_current_day_utc()

    stmt = select(
        func.coalesce(func.sum(Run.cost_usd), 0.0),
        func.count(Run.id),
    ).where(
        Run.agent_id == agent_id,
        Run.started_at >= since,
    )
    result = await session.execute(stmt)
    total_cost, total_count = result.one()
    return float(total_cost), int(total_count)


async def get_agent_budget_status(
    session: AsyncSession,
    agent: Agent,
) -> AgentBudgetStatusResponse:
    """Compute financial usage, budget ceilings, and circuit-breaker flags for an agent."""
    daily_spend, run_count = await get_daily_spend(session, agent.id)

    max_per_run: float | None = None
    max_per_day: float | None = None

    # Fetch active spec to extract budget configuration
    if agent.current_version:
        stmt = select(AgentVersion).where(
            AgentVersion.agent_id == agent.id,
            AgentVersion.version == agent.current_version,
        )
        res = await session.execute(stmt)
        ver = res.scalar_one_or_none()
        if ver is not None:
            spec_body = ver.spec.get("spec", {})
            budget = spec_body.get("budget", {})
            if budget:
                max_per_run = budget.get("max_usd_per_run")
                max_per_day = budget.get("max_usd_per_day")

    remaining: float | None = None
    utilization_pct: float | None = None

    if max_per_day is not None and max_per_day > 0:
        remaining = max(0.0, max_per_day - daily_spend)
        utilization_pct = min(100.0, (daily_spend / max_per_day) * 100.0)

    return AgentBudgetStatusResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        is_active=agent.is_active,
        kill_switch_tripped=agent.kill_switch_tripped,
        kill_switch_reason=agent.kill_switch_reason,
        kill_switch_tripped_at=agent.kill_switch_tripped_at,
        max_usd_per_run=max_per_run,
        max_usd_per_day=max_per_day,
        daily_spend_usd=round(daily_spend, 6),
        daily_runs_count=run_count,
        daily_budget_remaining_usd=round(remaining, 6) if remaining is not None else None,
        daily_budget_utilization_pct=(
            round(utilization_pct, 2) if utilization_pct is not None else None
        ),
    )


async def get_global_kill_switch(
    session: AsyncSession,
) -> GlobalKillSwitchStatus:
    """Retrieve the operational status of the platform-wide emergency stop."""
    stmt = select(SystemSetting).where(SystemSetting.key == GLOBAL_KILL_SWITCH_KEY)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()
    if setting is None:
        return GlobalKillSwitchStatus(enabled=False)

    val = setting.value or {}
    return GlobalKillSwitchStatus(
        enabled=bool(val.get("enabled", False)),
        reason=val.get("reason"),
        tripped_at=val.get("tripped_at"),
        operator=val.get("operator"),
    )


async def set_global_kill_switch(
    session: AsyncSession,
    enabled: bool,
    reason: str | None = None,
    operator: str = "system",
) -> GlobalKillSwitchStatus:
    """Toggle the platform-wide emergency stop switch."""
    stmt = select(SystemSetting).where(SystemSetting.key == GLOBAL_KILL_SWITCH_KEY)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    now_iso = datetime.now(UTC).isoformat()
    payload: dict[str, Any] = {
        "enabled": enabled,
        "reason": reason,
        "tripped_at": now_iso if enabled else None,
        "operator": operator,
    }

    if setting is None:
        setting = SystemSetting(
            key=GLOBAL_KILL_SWITCH_KEY,
            value=payload,
            updated_at=datetime.now(UTC),
        )
        session.add(setting)
    else:
        setting.value = payload
        setting.updated_at = datetime.now(UTC)

    await session.commit()
    return GlobalKillSwitchStatus(
        enabled=enabled,
        reason=reason,
        tripped_at=now_iso if enabled else None,
        operator=operator,
    )


async def trip_agent_kill_switch(
    session: AsyncSession,
    agent: Agent,
    reason: str,
    operator: str = "system",
) -> Agent:
    """Trip an agent-specific kill switch, halting execution immediately."""
    agent.kill_switch_tripped = True
    agent.is_active = False
    agent.kill_switch_reason = f"[{operator}] {reason}"
    agent.kill_switch_tripped_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(agent)
    return agent


async def resume_agent(
    session: AsyncSession,
    agent: Agent,
    operator: str = "system",
) -> Agent:
    """Clear an agent kill switch and reactivate the agent."""
    agent.kill_switch_tripped = False
    agent.is_active = True
    agent.kill_switch_reason = None
    agent.kill_switch_tripped_at = None
    await session.commit()
    await session.refresh(agent)
    return agent


async def check_pre_flight_budget_and_kill_switch(
    session: AsyncSession,
    agent: Agent,
    spec: dict[str, Any],
) -> tuple[bool, str | None]:
    """Evaluate pre-flight circuit-breakers before an agent run starts.

    Returns (is_allowed: bool, rejection_reason: str | None).
    """
    # 1. Global Kill Switch
    global_status = await get_global_kill_switch(session)
    if global_status.enabled:
        reason = global_status.reason or "halted by operator"
        return False, f"kill_switch_tripped: Global emergency stop is active ({reason})"

    # 2. Agent Kill Switch
    if agent.kill_switch_tripped or not agent.is_active:
        reason = agent.kill_switch_reason or "Emergency stop triggered"
        return False, f"kill_switch_tripped: Agent '{agent.name}' is halted ({reason})"

    # 3. Daily Spend Limit
    spec_body = spec.get("spec", {})
    budget = spec_body.get("budget", {})
    if budget:
        max_usd_per_day = budget.get("max_usd_per_day")
        if max_usd_per_day is not None and max_usd_per_day > 0:
            daily_spend, _ = await get_daily_spend(session, agent.id)
            if daily_spend >= max_usd_per_day:
                err_msg = (
                    f"budget_exceeded: Daily budget limit of ${max_usd_per_day:.2f} reached "
                    f"(current spend: ${daily_spend:.2f})"
                )
                return False, err_msg

    return True, None


def check_post_run_budget_breaker(
    run_cost_usd: float,
    spec: dict[str, Any],
) -> tuple[bool, str | None]:
    """Evaluate if a single execution run breached its allocated per-run budget ceiling.

    Returns (is_allowed: bool, violation_reason: str | None).
    """
    spec_body = spec.get("spec", {})
    budget = spec_body.get("budget", {})
    if not budget:
        return True, None

    max_usd_per_run = budget.get("max_usd_per_run")
    if max_usd_per_run is not None and max_usd_per_run > 0 and run_cost_usd > max_usd_per_run:
        err_msg = (
            f"budget_exceeded: Run cost of ${run_cost_usd:.4f} "
            f"exceeded maximum per-run budget of ${max_usd_per_run:.2f}"
        )
        return False, err_msg

    return True, None
