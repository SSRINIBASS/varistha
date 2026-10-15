"""Service layer for triggering and managing agent execution runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.context import Context
from runtime.interface import RunContext
from shared.db.models import Agent, AgentVersion, Approval, Run, SystemSetting
from shared.telemetry import (
    GEN_AI_USAGE_TOTAL_TOKENS,
    VARISTHA_AGENT_ID,
    VARISTHA_AGENT_NAME,
    VARISTHA_AGENT_VERSION,
    VARISTHA_APPROVAL_REQUIRED,
    VARISTHA_APPROVAL_STATUS,
    VARISTHA_AUTONOMY,
    VARISTHA_BUDGET_EXCEEDED,
    VARISTHA_COST_USD,
    VARISTHA_KILL_SWITCH_TRIPPED,
    VARISTHA_RUN_ID,
    VARISTHA_STAGE,
    VARISTHA_TRIGGER_TYPE,
    capture_run_spans,
    get_tracer,
    save_captured_spans,
)
from sqlalchemy import func, select

if TYPE_CHECKING:
    from runtime.interface import Runtime
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentNotFoundError(Exception):
    """Raised when the target agent does not exist."""


class NoVersionFoundError(Exception):
    """Raised when the agent has no published versions to execute."""


class KillSwitchTrippedError(Exception):
    """Raised when execution is halted by an agent or global kill switch."""


class BudgetExceededError(Exception):
    """Raised when an execution cannot start because the daily budget limit is exhausted."""


def is_valid_uuid(val: str) -> bool:
    """Return True if val is a valid UUID string."""
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False


async def resolve_agent(session: AsyncSession, id_or_name: str) -> Agent | None:
    """Fetch an agent by UUID or unique slug name."""
    if is_valid_uuid(id_or_name):
        stmt = select(Agent).where(Agent.id == uuid.UUID(id_or_name))
        result = await session.execute(stmt)
        agent = result.scalar_one_or_none()
        if agent is not None:
            return agent

    stmt = select(Agent).where(Agent.name == id_or_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_active_version(session: AsyncSession, agent: Agent) -> AgentVersion | None:
    """Retrieve the current active version snapshot for an agent."""
    if agent.current_version:
        stmt = select(AgentVersion).where(
            AgentVersion.agent_id == agent.id,
            AgentVersion.version == agent.current_version,
        )
        result = await session.execute(stmt)
        ver = result.scalar_one_or_none()
        if ver is not None:
            return ver

    # Fallback to newest version if current_version is not set
    stmt = (
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent.id)
        .order_by(AgentVersion.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def trigger_agent_run(
    session: AsyncSession,
    id_or_name: str,
    input_data: dict[str, Any],
    trigger_type: str,
    runtime: Runtime,
) -> Run:
    """Create a Run record and execute the agent through the runtime engine."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise AgentNotFoundError(f"Agent '{id_or_name}' not found")

    version = await get_active_version(session, agent)
    if version is None:
        raise NoVersionFoundError(
            f"Agent '{agent.name}' has no published versions. Publish a version before running."
        )

    spec = version.spec
    spec_body = spec.get("spec", {})
    model = spec_body.get("model", {}).get("primary", "gpt-4o")
    instructions = spec_body.get("instructions", "")

    now = datetime.now(UTC)

    # 1. Pre-flight check: Global kill switch
    stmt_global = select(SystemSetting).where(SystemSetting.key == "global_kill_switch")
    res_global = await session.execute(stmt_global)
    global_setting = res_global.scalar_one_or_none()
    if global_setting and global_setting.value and global_setting.value.get("enabled"):
        reason = global_setting.value.get("reason") or "Emergency stop"
        raise KillSwitchTrippedError(
            f"kill_switch_tripped: Global emergency stop is active ({reason})"
        )

    # 2. Pre-flight check: Agent kill switch and active status
    if agent.kill_switch_tripped or not agent.is_active:
        reason = agent.kill_switch_reason or "Emergency stop"
        raise KillSwitchTrippedError(
            f"kill_switch_tripped: Agent '{agent.name}' is halted ({reason})"
        )

    # 3. Pre-flight check: Daily budget limit
    budget_cfg = spec_body.get("budget", {})
    max_usd_per_day = budget_cfg.get("max_usd_per_day") if budget_cfg else None
    if max_usd_per_day is not None and max_usd_per_day > 0:
        start_of_day = datetime.combine(now.date(), time.min, tzinfo=UTC)
        stmt_daily = select(func.coalesce(func.sum(Run.cost_usd), 0.0)).where(
            Run.agent_id == agent.id,
            Run.started_at >= start_of_day,
        )
        res_daily = await session.execute(stmt_daily)
        current_daily_spend = float(res_daily.scalar_one())
        if current_daily_spend >= max_usd_per_day:
            raise BudgetExceededError(
                f"budget_exceeded: Daily budget limit of ${max_usd_per_day:.2f} reached "
                f"(current spend: ${current_daily_spend:.2f})"
            )
    run = Run(
        agent_id=agent.id,
        agent_version_id=version.id,
        status="running",
        trigger_type=trigger_type,
        input=input_data,
        started_at=now,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    context = RunContext(
        run_id=run.id,
        agent_id=agent.id,
        agent_name=agent.name,
        model=model,
        instructions=instructions,
        input_data=input_data,
        spec_snapshot=spec,
    )

    tracer = get_tracer("varistha.runtime")
    with (
        capture_run_spans(run.id) as captured_spans,
        tracer.start_as_current_span(
            "agent.run",
            context=Context(),
            attributes={
                VARISTHA_RUN_ID: str(run.id),
                VARISTHA_AGENT_ID: str(agent.id),
                VARISTHA_AGENT_NAME: agent.name,
                VARISTHA_AGENT_VERSION: version.version,
                VARISTHA_STAGE: spec.get("metadata", {}).get("stage", "prototype"),
                VARISTHA_AUTONOMY: spec_body.get("autonomy", "L1"),
                VARISTHA_TRIGGER_TYPE: trigger_type,
            },
        ) as root_span,
    ):
        result = await runtime.execute(context)
        root_span.set_attribute(VARISTHA_COST_USD, result.cost_usd)
        root_span.set_attribute(GEN_AI_USAGE_TOTAL_TOKENS, result.total_tokens)
        if result.status == "completed":
            root_span.set_status(trace.StatusCode.OK)
        elif result.status == "waiting_approval":
            root_span.set_attribute(VARISTHA_APPROVAL_REQUIRED, True)
            root_span.set_attribute(VARISTHA_APPROVAL_STATUS, "pending")
            root_span.set_status(trace.StatusCode.OK)
        else:
            if result.error and "budget_exceeded" in result.error:
                root_span.set_attribute(VARISTHA_BUDGET_EXCEEDED, True)
            if result.error and "kill_switch_tripped" in result.error:
                root_span.set_attribute(VARISTHA_KILL_SWITCH_TRIPPED, True)
            root_span.set_status(trace.StatusCode.ERROR, result.error or "Run failed")

    run.status = result.status
    run.output = result.output
    run.cost_usd = result.cost_usd
    run.total_tokens = result.total_tokens
    run.error = result.error

    if result.status == "waiting_approval":
        run.completed_at = None
        proposed = result.proposed_action or {}
        approval = Approval(
            run_id=run.id,
            agent_id=agent.id,
            status="pending",
            action_type=proposed.get("action_type", "outbound_action"),
            tool_name=proposed.get("tool_name"),
            description=proposed.get("description", "Action requires human approval"),
            proposed_payload=proposed.get("payload", result.output),
            created_at=datetime.now(UTC),
        )
        session.add(approval)
    else:
        run.completed_at = datetime.now(UTC)

    await save_captured_spans(session, captured_spans, run.id)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run(session: AsyncSession, run_id: uuid.UUID) -> Run | None:
    """Retrieve a run by its UUID."""
    stmt = select(Run).where(Run.id == run_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_runs_for_agent(
    session: AsyncSession,
    agent_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Run], int]:
    """List runs for a specific agent with pagination."""
    count_stmt = select(func.count(Run.id)).where(Run.agent_id == agent_id)
    count_res = await session.execute(count_stmt)
    total = count_res.scalar_one()

    query = (
        select(Run)
        .where(Run.agent_id == agent_id)
        .order_by(Run.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(query)
    runs = list(res.scalars().all())

    return runs, total


async def list_all_runs(
    session: AsyncSession,
    agent_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Run], int]:
    """List runs across all agents with optional filtering and pagination."""
    count_stmt = select(func.count(Run.id))
    query = select(Run).order_by(Run.created_at.desc())

    if agent_id is not None:
        count_stmt = count_stmt.where(Run.agent_id == agent_id)
        query = query.where(Run.agent_id == agent_id)

    if status is not None:
        count_stmt = count_stmt.where(Run.status == status)
        query = query.where(Run.status == status)

    count_res = await session.execute(count_stmt)
    total = count_res.scalar_one()

    query = query.limit(limit).offset(offset)
    res = await session.execute(query)
    runs = list(res.scalars().all())

    return runs, total
