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
    GateCheckResponse,
    GateEvaluationResponse,
    PromoteAgentRequest,
    PromoteAgentResponse,
    StageTransitionResponse,
)
from registry.service import (
    DuplicateVersionError,
    GateCheckFailedError,
    create_or_update_agent,
    evaluate_gates_for_agent,
    get_stage_history,
    get_version,
    list_agents,
    list_versions,
    promote_agent,
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


@router.post(
    "/{id_or_name}/promote",
    response_model=PromoteAgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Promote or transition agent lifecycle stage",
)
async def promote_agent_endpoint(
    id_or_name: str,
    payload: PromoteAgentRequest,
    session: DbSession,
) -> PromoteAgentResponse:
    """Transition an agent to a new lifecycle stage under gate evaluation."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    try:
        updated_agent, transition, gate_result = await promote_agent(
            session=session,
            agent=agent,
            to_stage=payload.to_stage,
            promoted_by=payload.promoted_by,
            reason=payload.reason,
            replacement=payload.replacement,
            kill_switch_verified=payload.kill_switch_verified,
            secrets_revoked=payload.secrets_revoked,
        )
    except GateCheckFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "detail": str(exc),
                "evaluation": exc.gate_result.to_dict(),
            },
        ) from exc

    latest_spec = updated_agent.versions[0].spec if updated_agent.versions else None

    agent_detail = AgentDetailResponse(
        id=updated_agent.id,
        name=updated_agent.name,
        description=updated_agent.description,
        owner=updated_agent.owner,
        stage=updated_agent.stage,
        current_version=updated_agent.current_version,
        created_at=updated_agent.created_at,
        updated_at=updated_agent.updated_at,
        version_count=len(updated_agent.versions),
        latest_spec=latest_spec,
    )

    transition_resp = StageTransitionResponse(
        id=transition.id,
        agent_id=transition.agent_id,
        from_stage=transition.from_stage,
        to_stage=transition.to_stage,
        promoted_by=transition.promoted_by,
        reason=transition.reason,
        gate_results=transition.gate_results,
        created_at=transition.created_at,
    )

    evaluation_resp = GateEvaluationResponse(
        allowed=gate_result.allowed,
        from_stage=gate_result.from_stage,
        to_stage=gate_result.to_stage,
        is_rollback=gate_result.is_rollback,
        checks=[
            GateCheckResponse(name=c.name, passed=c.passed, message=c.message)
            for c in gate_result.checks
        ],
        error_message=gate_result.error_message,
    )

    return PromoteAgentResponse(
        agent=agent_detail,
        transition=transition_resp,
        evaluation=evaluation_resp,
    )


@router.get(
    "/{id_or_name}/history",
    response_model=list[StageTransitionResponse],
    summary="Get lifecycle stage transition audit history",
)
async def get_agent_history_endpoint(
    id_or_name: str,
    session: DbSession,
) -> list[StageTransitionResponse]:
    """Retrieve the immutable lifecycle stage audit trail for an agent."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    transitions = await get_stage_history(session, agent.id)
    return [
        StageTransitionResponse(
            id=t.id,
            agent_id=t.agent_id,
            from_stage=t.from_stage,
            to_stage=t.to_stage,
            promoted_by=t.promoted_by,
            reason=t.reason,
            gate_results=t.gate_results,
            created_at=t.created_at,
        )
        for t in transitions
    ]


@router.get(
    "/{id_or_name}/gates/{target_stage}",
    response_model=GateEvaluationResponse,
    summary="Dry-run preview of lifecycle promotion gates",
)
async def preview_gates_endpoint(
    id_or_name: str,
    target_stage: str,
    session: DbSession,
    replacement: Annotated[
        str | None,
        Query(description="Replacement agent slug (for deprecation preview)."),
    ] = None,
    kill_switch_verified: Annotated[
        bool | None,
        Query(description="Kill switch test status."),
    ] = None,
    secrets_revoked: Annotated[
        bool | None,
        Query(description="Secrets revocation status."),
    ] = None,
) -> GateEvaluationResponse:
    """Evaluate promotion gates without mutating agent state (ideal for UI checklists)."""
    agent = await resolve_agent(session, id_or_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id_or_name}' not found",
        )

    gate_result = await evaluate_gates_for_agent(
        session=session,
        agent=agent,
        target_stage=target_stage,
        replacement=replacement,
        kill_switch_verified=kill_switch_verified,
        secrets_revoked=secrets_revoked,
    )

    return GateEvaluationResponse(
        allowed=gate_result.allowed,
        from_stage=gate_result.from_stage,
        to_stage=gate_result.to_stage,
        is_rollback=gate_result.is_rollback,
        checks=[
            GateCheckResponse(name=c.name, passed=c.passed, message=c.message)
            for c in gate_result.checks
        ],
        error_message=gate_result.error_message,
    )
