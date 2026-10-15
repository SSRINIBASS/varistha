"""Pydantic schemas for the Agent Registry API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentResponse(BaseModel):
    """Public summary representation of a registered agent."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str = Field(description="Unique agent slug name.")
    description: str | None = Field(default=None, description="Human-readable description.")
    owner: str = Field(description="Email of the agent owner.")
    stage: str = Field(description="Current lifecycle stage.")
    current_version: str | None = Field(default=None, description="Active semver version.")
    created_at: datetime
    updated_at: datetime
    version_count: int = Field(default=0, description="Total number of published versions.")


class AgentDetailResponse(AgentResponse):
    """Detailed agent representation including latest spec snapshot."""

    latest_spec: dict[str, Any] | None = Field(
        default=None,
        description="Full raw AgentSpec snapshot of the current version.",
    )


class AgentListResponse(BaseModel):
    """Paginated list of agents."""

    items: list[AgentResponse]
    total: int
    limit: int
    offset: int


class AgentVersionSummaryResponse(BaseModel):
    """Summary of an immutable agent version snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    version: str
    created_at: datetime


class AgentVersionDetailResponse(AgentVersionSummaryResponse):
    """Detailed view of an agent version including the immutable spec."""

    spec: dict[str, Any] = Field(description="The complete AgentSpec dictionary snapshot.")


class ValidationErrorDetail(BaseModel):
    """Error payload returned when spec validation fails."""

    detail: str = "Agent spec validation failed"
    errors: list[str] = Field(description="List of location-prefixed validation errors.")


class PromoteAgentRequest(BaseModel):
    """Request payload to promote or rollback an agent to a target lifecycle stage."""

    to_stage: str = Field(
        description="Target stage (draft, prototype, staging, production, deprecated, retired).",
    )
    promoted_by: str = Field(
        description="Email or username of the operator requesting the transition.",
    )
    reason: str | None = Field(
        default=None,
        description="Explanation or migration notes (mandatory for rollbacks).",
    )
    replacement: str | None = Field(
        default=None,
        description="Replacement agent slug or reference (for deprecation).",
    )
    kill_switch_verified: bool | None = Field(
        default=None,
        description="Operator confirmation of kill switch test (required for production).",
    )
    secrets_revoked: bool | None = Field(
        default=None,
        description="Operator confirmation that credentials were revoked (for retirement).",
    )


class GateCheckResponse(BaseModel):
    """Single gate check result."""

    name: str
    passed: bool
    message: str


class GateEvaluationResponse(BaseModel):
    """Full gate evaluation checklist outcome."""

    allowed: bool
    from_stage: str
    to_stage: str
    is_rollback: bool
    checks: list[GateCheckResponse]
    error_message: str | None = None


class StageTransitionResponse(BaseModel):
    """Audit log record for an agent lifecycle stage change."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    from_stage: str
    to_stage: str
    promoted_by: str
    reason: str | None = None
    gate_results: list[dict[str, Any]]
    created_at: datetime


class PromoteAgentResponse(BaseModel):
    """Response returned upon successful stage promotion."""

    agent: AgentDetailResponse
    transition: StageTransitionResponse
    evaluation: GateEvaluationResponse


class SpecDiffRequest(BaseModel):
    """Request payload to preview a spec diff against an existing version."""

    spec: dict[str, Any] = Field(description="Candidate AgentSpec dictionary to diff.")
    base_version: str | None = Field(
        default=None,
        description="Base version to compare against. If None, uses current active version.",
    )


class DiffEntryResponse(BaseModel):
    """A single field diff result."""

    field: str = Field(description="Dotted path of the changed field.")
    change_type: str = Field(description="added, removed, or modified.")
    old_value: Any = Field(default=None, description="Previous value or None.")
    new_value: Any = Field(default=None, description="New value or None.")
    is_breaking: bool = Field(default=False, description="Whether this change is breaking.")
    breaking_reason: str | None = Field(
        default=None, description="Explanation if this change is breaking."
    )
    description: str = Field(description="Human-readable description of the change.")


class SpecDiffResponse(BaseModel):
    """Structured response comparing two agent specifications."""

    from_version: str | None = Field(default=None, description="Base version string.")
    to_version: str | None = Field(default=None, description="Target version string.")
    has_changes: bool = Field(description="True if any difference was detected.")
    has_breaking_changes: bool = Field(description="True if any breaking difference exists.")
    summary: dict[str, int] = Field(
        description="Counts of total, added, removed, modified, breaking."
    )
    entries: list[DiffEntryResponse] = Field(description="All detected diff entries.")
    breaking_entries: list[DiffEntryResponse] = Field(
        description="Filtered list of breaking diff entries."
    )
