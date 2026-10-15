"""FastAPI router for governance guardrail policies."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from governance.policies.schemas import (
    PolicyInfoResponse,
    PolicyListResponse,
    PolicyTestRequest,
    PolicyTestResponse,
)
from shared.guardrails import (
    PolicyContext,
    PolicyHook,
    default_policy_engine,
    default_policy_registry,
)

router = APIRouter(prefix="/api/v1/policies", tags=["Governance: Guardrails & Policies"])


@router.get(
    "",
    response_model=PolicyListResponse,
    summary="List Guardrail Policies",
    description="List all registered platform guardrail policies and their supported hooks.",
)
async def list_policies() -> PolicyListResponse:
    """Return all registered guardrail policies."""
    policies = default_policy_registry.list_policies()
    items = [
        PolicyInfoResponse(
            name=p.name,
            description=p.description,
            supported_hooks=[h.value for h in p.supported_hooks],
        )
        for p in policies
    ]
    return PolicyListResponse(policies=items, total=len(items))


@router.post(
    "/test",
    response_model=PolicyTestResponse,
    summary="Test Guardrail Policy",
    description="Interactively evaluate a guardrail policy against sample data or text.",
)
async def test_policy(payload: PolicyTestRequest) -> PolicyTestResponse:
    """Evaluate a guardrail policy interactively."""
    policy = default_policy_registry.get(payload.policy_name)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardrail policy '{payload.policy_name}' not found",
        )

    try:
        hook_enum = PolicyHook(payload.hook)
    except ValueError:
        allowed = [h.value for h in PolicyHook]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid policy hook '{payload.hook}'. Expected one of: {allowed}",
        ) from None

    ctx = PolicyContext(hook=hook_enum)
    result = await default_policy_engine.evaluate(
        [payload.policy_name], hook=hook_enum, data=payload.payload, context=ctx
    )

    return PolicyTestResponse(
        policy_name=payload.policy_name,
        passed=result.passed,
        action=result.action,
        modified_data=result.modified_data,
        violations=result.violations,
        metadata=result.metadata,
    )
