"""Spec diffing service operations for the Agent Registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from registry.service import VersionNotFoundError, get_version
from shared.db.models import Agent, AgentVersion
from sqlalchemy import select

from spec import SpecDiff, diff_specs, validate_spec

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def diff_agent_versions(
    session: AsyncSession,
    agent: Agent,
    v1_str: str,
    v2_str: str,
) -> SpecDiff:
    """Compare two immutable published versions of an agent.

    Args:
        session: Active async database session.
        agent: Resolved Agent instance.
        v1_str: Base version string (e.g. "0.1.0").
        v2_str: Target version string (e.g. "0.2.0").

    Returns:
        SpecDiff containing all detected field differences and breaking change classifications.

    Raises:
        VersionNotFoundError: If either version snapshot does not exist.

    """
    ver1 = await get_version(session, agent.id, v1_str)
    if ver1 is None:
        raise VersionNotFoundError(f"Version '{v1_str}' not found for agent '{agent.name}'")

    ver2 = await get_version(session, agent.id, v2_str)
    if ver2 is None:
        raise VersionNotFoundError(f"Version '{v2_str}' not found for agent '{agent.name}'")

    return diff_specs(ver1.spec, ver2.spec)


async def preview_agent_diff(
    session: AsyncSession,
    agent: Agent,
    candidate_spec: dict[str, Any],
    base_version_str: str | None = None,
) -> SpecDiff:
    """Compare a candidate specification against an existing version of an agent.

    Args:
        session: Active async database session.
        agent: Resolved Agent instance.
        candidate_spec: Raw or validated candidate spec dictionary.
        base_version_str: Specific base version string, or None to use active version.

    Returns:
        SpecDiff comparing base spec to candidate spec.

    Raises:
        VersionNotFoundError: If the specified base version does not exist.

    """
    # Validate candidate spec first to ensure well-formedness
    validated_candidate = validate_spec(candidate_spec)

    base_spec_dict: dict[str, Any]
    if base_version_str is not None:
        base_ver = await get_version(session, agent.id, base_version_str)
        if base_ver is None:
            raise VersionNotFoundError(
                f"Base version '{base_version_str}' not found for agent '{agent.name}'"
            )
        base_spec_dict = base_ver.spec
    else:
        # Fetch the current active / latest version
        stmt = (
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent.id)
            .order_by(AgentVersion.created_at.desc())
        )
        res = await session.execute(stmt)
        latest_ver = res.scalars().first()
        if latest_ver is None:
            raise VersionNotFoundError(f"No existing versions found for agent '{agent.name}'")
        base_spec_dict = latest_ver.spec

    return diff_specs(base_spec_dict, validated_candidate)
