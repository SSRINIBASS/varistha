"""Service layer for triggering and managing agent execution runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from runtime.interface import RunContext
from shared.db.models import Agent, AgentVersion, Run
from sqlalchemy import func, select

if TYPE_CHECKING:
    from runtime.interface import Runtime
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentNotFoundError(Exception):
    """Raised when the target agent does not exist."""


class NoVersionFoundError(Exception):
    """Raised when the agent has no published versions to execute."""


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

    result = await runtime.execute(context)

    run.status = result.status
    run.output = result.output
    run.cost_usd = result.cost_usd
    run.total_tokens = result.total_tokens
    run.error = result.error
    run.completed_at = datetime.now(UTC)

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
