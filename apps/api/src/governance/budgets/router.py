"""FastAPI router for budget monitoring and emergency kill switches."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from governance.budgets.schemas import (
    AgentBudgetStatusResponse,
    GlobalKillSwitchRequest,
    GlobalKillSwitchStatus,
    KillSwitchRequest,
    KillSwitchResponse,
)
from governance.budgets.service import (
    get_agent_budget_status,
    get_global_kill_switch,
    resume_agent,
    set_global_kill_switch,
    trip_agent_kill_switch,
)
from shared.db.models import Agent
from shared.db.session import get_db_session
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Governance: Budgets & Circuit Breakers"])

DbSession = Annotated["AsyncSession", Depends(get_db_session)]


def is_valid_uuid(val: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError):
        return False


async def resolve_agent(session: AsyncSession, id_or_name: str) -> Agent | None:
    """Resolve an Agent by UUID or unique name slug."""
    if is_valid_uuid(id_or_name):
        stmt = select(Agent).where(Agent.id == uuid.UUID(id_or_name))
        res = await session.execute(stmt)
        agent = res.scalar_one_or_none()
        if agent is not None:
            return agent

    stmt = select(Agent).where(Agent.name == id_or_name)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


@router.get(
    "/api/v1/agents/{id_or_name}/budget",
    response_model=AgentBudgetStatusResponse,
    summary="Get Agent Budget Status",
    description="Inspect daily USD spend, remaining balance, and circuit-breaker flags.",
)
async def get_budget_status(
    id_or_name: str,
    session: DbSession,
) -> AgentBudgetStatusResponse:
    """Return financial usage, budget limits, and kill switch status."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )
    return await get_agent_budget_status(session, agent)


@router.post(
    "/api/v1/agents/{id_or_name}/kill",
    response_model=KillSwitchResponse,
    summary="Trip Agent Kill Switch",
    description="Halt an agent immediately, preventing any new runs or outbound side-effects.",
)
async def kill_agent(
    id_or_name: str,
    payload: KillSwitchRequest,
    session: DbSession,
) -> KillSwitchResponse:
    """Trip the kill switch for an agent."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    updated = await trip_agent_kill_switch(
        session,
        agent,
        reason=payload.reason,
        operator=payload.operator or "system",
    )
    return KillSwitchResponse(
        agent_id=updated.id,
        agent_name=updated.name,
        is_active=updated.is_active,
        kill_switch_tripped=updated.kill_switch_tripped,
        reason=updated.kill_switch_reason,
        tripped_at=updated.kill_switch_tripped_at,
        operator=payload.operator or "system",
    )


@router.post(
    "/api/v1/agents/{id_or_name}/resume",
    response_model=KillSwitchResponse,
    summary="Resume Agent Execution",
    description="Clear an agent's kill switch and reactivate execution permissions.",
)
async def resume_agent_route(
    id_or_name: str,
    session: DbSession,
    operator: Annotated[str, Query(description="Operator identity resuming the agent")] = "system",
) -> KillSwitchResponse:
    """Reset the kill switch for an agent."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    updated = await resume_agent(
        session,
        agent,
        operator=operator,
    )
    return KillSwitchResponse(
        agent_id=updated.id,
        agent_name=updated.name,
        is_active=updated.is_active,
        kill_switch_tripped=updated.kill_switch_tripped,
        reason=None,
        tripped_at=None,
        operator=operator,
    )


@router.get(
    "/api/v1/system/kill-switch",
    response_model=GlobalKillSwitchStatus,
    summary="Get Global Kill Switch Status",
    description="Inspect whether the platform-wide emergency stop is currently active.",
)
async def get_system_kill_switch(
    session: DbSession,
) -> GlobalKillSwitchStatus:
    """Check platform-wide emergency stop status."""
    return await get_global_kill_switch(session)


@router.post(
    "/api/v1/system/kill-switch",
    response_model=GlobalKillSwitchStatus,
    summary="Toggle Global Kill Switch",
    description="Emergency stop or resume all agent executions across the entire control plane.",
)
async def toggle_system_kill_switch(
    payload: GlobalKillSwitchRequest,
    session: DbSession,
) -> GlobalKillSwitchStatus:
    """Set platform-wide emergency stop status."""
    return await set_global_kill_switch(
        session,
        enabled=payload.enabled,
        reason=payload.reason,
        operator=payload.operator or "system",
    )
