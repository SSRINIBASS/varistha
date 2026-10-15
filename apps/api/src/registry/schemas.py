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
