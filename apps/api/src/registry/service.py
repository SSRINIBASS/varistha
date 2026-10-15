"""Business logic and database access for the Agent Registry."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from shared.db.models import Agent, AgentVersion
from sqlalchemy import func, select

from spec import AgentSpec, validate_spec

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AgentNotFoundError(Exception):
    """Raised when an agent cannot be resolved by ID or slug name."""


class DuplicateVersionError(Exception):
    """Raised when attempting to overwrite an immutable agent version."""


class VersionNotFoundError(Exception):
    """Raised when a specific version snapshot is not found."""


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


async def list_agents(
    session: AsyncSession,
    stage: str | None = None,
    owner: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Agent], int]:
    """List agents with optional filtering and pagination."""
    query = select(Agent)
    count_query = select(func.count(Agent.id))

    if stage:
        query = query.where(Agent.stage == stage)
        count_query = count_query.where(Agent.stage == stage)

    if owner:
        query = query.where(Agent.owner == owner)
        count_query = count_query.where(Agent.owner == owner)

    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Agent.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    agents = list(result.scalars().all())

    return agents, total


async def create_or_update_agent(
    session: AsyncSession,
    raw_spec: dict[str, Any],
) -> tuple[Agent, AgentVersion, bool]:
    """Validate spec and create agent or register a new immutable version.

    Returns:
        tuple[Agent, AgentVersion, is_created]

    """
    spec: AgentSpec = validate_spec(raw_spec)
    agent_name = spec.metadata.name
    version_str = spec.metadata.version

    # Check if agent exists
    stmt = select(Agent).where(Agent.name == agent_name)
    result = await session.execute(stmt)
    agent = result.scalar_one_or_none()

    if agent is None:
        agent = Agent(
            name=agent_name,
            description=spec.spec.role,
            owner=spec.metadata.owner,
            stage=spec.metadata.stage,
            current_version=version_str,
        )
        session.add(agent)
        await session.flush()

        version = AgentVersion(
            agent_id=agent.id,
            version=version_str,
            spec=spec.model_dump(mode="json"),
        )
        session.add(version)
        await session.commit()
        await session.refresh(agent)
        return agent, version, True

    # Agent exists - check if version is already published
    v_stmt = select(AgentVersion).where(
        AgentVersion.agent_id == agent.id,
        AgentVersion.version == version_str,
    )
    v_result = await session.execute(v_stmt)
    existing_version = v_result.scalar_one_or_none()

    if existing_version is not None:
        msg = (
            f"Version '{version_str}' already exists for agent '{agent_name}'. "
            "Agent specs are immutable once published."
        )
        raise DuplicateVersionError(msg)

    # Publish new version
    version = AgentVersion(
        agent_id=agent.id,
        version=version_str,
        spec=spec.model_dump(mode="json"),
    )
    agent.current_version = version_str
    agent.owner = spec.metadata.owner
    agent.stage = spec.metadata.stage
    if spec.spec.role:
        agent.description = spec.spec.role

    session.add(version)
    await session.commit()
    await session.refresh(agent)
    return agent, version, False


async def get_version(
    session: AsyncSession,
    agent_id: uuid.UUID,
    version_str: str,
) -> AgentVersion | None:
    """Fetch an exact immutable version snapshot for an agent."""
    stmt = select(AgentVersion).where(
        AgentVersion.agent_id == agent_id,
        AgentVersion.version == version_str,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_versions(
    session: AsyncSession,
    agent_id: uuid.UUID,
) -> list[AgentVersion]:
    """List all version snapshots for an agent, newest first."""
    stmt = (
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
