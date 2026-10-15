"""Pydantic schemas for guardrail policies API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyInfoResponse(BaseModel):
    """Metadata describing a registered guardrail policy."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Unique policy identifier (e.g. pii-redact).")
    description: str = Field(..., description="Description of the policy's checks.")
    supported_hooks: list[str] = Field(
        ..., description="Supported execution hooks: input, output, tools."
    )


class PolicyListResponse(BaseModel):
    """List response of registered policies."""

    policies: list[PolicyInfoResponse] = Field(..., description="Registered policies.")
    total: int = Field(..., description="Total policy count.")


class PolicyTestRequest(BaseModel):
    """Request to test a guardrail policy against sample data."""

    policy_name: str = Field(..., description="Name of policy to evaluate.")
    hook: str = Field(default="input", description="Hook type: input, output, or tools.")
    payload: Any = Field(..., description="Text, JSON, or list payload to evaluate.")


class PolicyTestResponse(BaseModel):
    """Outcome of testing a guardrail policy."""

    policy_name: str = Field(..., description="Name of policy evaluated.")
    passed: bool = Field(..., description="Whether payload passed.")
    action: str = Field(..., description="Action taken: allow, redact, or block.")
    modified_data: Any | None = Field(
        default=None, description="Sanitized or redacted data if altered."
    )
    violations: list[str] = Field(default_factory=list, description="Violation descriptions.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Evaluation metadata.")
