"""FastAPI router for Agent Registry endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from registry.schemas import (
    AgentDetailResponse,
    AgentListResponse,
    AgentResponse,
    AgentVersionDetailResponse,
    AgentVersionSummaryResponse,
)
from registry.service import (
    DuplicateVersionError,
    create_or_update_agent,
    get_version,
    list_agents,
    list_versions,
    resolve_agent,
)
from shared.db.session import get_db_session

from spec import SpecValidationError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

DbSession = Annotated["AsyncSession", Depends(get_db_session)]


@router.post(
    "",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register agent or publish new version",
)
async def register_agent(
    raw_spec: dict[str, Any],
    session: DbSession,
) -> AgentDetailResponse:
    """Validate an AgentSpec and register an agent or publish a new version."""
    try:
        agent, version, _ = await create_or_update_agent(session, raw_spec)
    except SpecValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": "Agent spec validation failed", "errors": exc.errors},
        ) from exc
    except DuplicateVersionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AgentDetailResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        owner=agent.owner,
        stage=agent.stage,
        current_version=agent.current_version,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        version_count=len(agent.versions),
        latest_spec=version.spec,
    )


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List registered agents",
)
async def get_agents(
    session: DbSession,
    stage: Annotated[str | None, Query(description="Filter by lifecycle stage.")] = None,
    owner: Annotated[str | None, Query(description="Filter by owner email.")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset.")] = 0,
) -> AgentListResponse:
    """List agents with optional filtering by stage and owner."""
    agents, total = await list_agents(
        session,
        stage=stage,
        owner=owner,
        limit=limit,
        offset=offset,
    )

    items = [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            owner=agent.owner,
            stage=agent.stage,
            current_version=agent.current_version,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            version_count=len(agent.versions),
        )
        for agent in agents
    ]

    return AgentListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{id_or_name}",
    response_model=AgentDetailResponse,
    summary="Get agent details",
)
async def get_agent(
    id_or_name: str,
    session: DbSession,
) -> AgentDetailResponse:
    """Retrieve an agent by its UUID or unique slug name."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    latest_spec = agent.versions[0].spec if agent.versions else None

    return AgentDetailResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        owner=agent.owner,
        stage=agent.stage,
        current_version=agent.current_version,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        version_count=len(agent.versions),
        latest_spec=latest_spec,
    )


@router.get(
    "/{id_or_name}/versions",
    response_model=list[AgentVersionSummaryResponse],
    summary="List versions of an agent",
)
async def get_agent_versions(
    id_or_name: str,
    session: DbSession,
) -> list[AgentVersionSummaryResponse]:
    """List all version snapshots for an agent, newest first."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    versions = await list_versions(session, agent.id)
    return [
        AgentVersionSummaryResponse(
            id=v.id,
            agent_id=v.agent_id,
            version=v.version,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get(
    "/{id_or_name}/versions/{version}",
    response_model=AgentVersionDetailResponse,
    summary="Get exact immutable version spec",
)
async def get_agent_version_detail(
    id_or_name: str,
    version: str,
    session: DbSession,
) -> AgentVersionDetailResponse:
    """Retrieve the exact immutable spec snapshot for a specific agent version."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    ver = await get_version(session, agent.id, version)
    if ver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version}' not found for agent '{agent.name}'",
        )

    return AgentVersionDetailResponse(
        id=ver.id,
        agent_id=ver.agent_id,
        version=ver.version,
        created_at=ver.created_at,
        spec=ver.spec,
    )


@router.post(
    "/{id_or_name}/versions",
    response_model=AgentVersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish new version for existing agent",
)
async def publish_agent_version(
    id_or_name: str,
    raw_spec: dict[str, Any],
    session: DbSession,
) -> AgentVersionDetailResponse:
    """Publish a new version for an existing agent."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    # Ensure spec name matches target agent
    if "metadata" in raw_spec and isinstance(raw_spec["metadata"], dict):
        spec_name = raw_spec["metadata"].get("name")
        if spec_name and spec_name != agent.name:
            err_msg = f"Spec metadata.name '{spec_name}' does not match target agent '{agent.name}'"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )
        raw_spec["metadata"]["name"] = agent.name

    try:
        _, version, _ = await create_or_update_agent(session, raw_spec)
    except SpecValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"detail": "Agent spec validation failed", "errors": exc.errors},
        ) from exc
    except DuplicateVersionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AgentVersionDetailResponse(
        id=version.id,
        agent_id=version.agent_id,
        version=version.version,
        created_at=version.created_at,
        spec=version.spec,
    )
