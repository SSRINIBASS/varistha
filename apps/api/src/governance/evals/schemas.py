"""Pydantic schemas for eval suites, runs, and results in governance."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvalSuiteCreate(BaseModel):
    """Payload to register or update an evaluation suite."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., max_length=100, description="Slug name of the evaluation suite.")
    agent_id: uuid.UUID = Field(..., description="Target agent UUID.")
    description: str | None = Field(default=None, description="Suite purpose.")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Evaluator configurations and metadata."
    )


class EvalSuiteResponse(BaseModel):
    """Response representing an evaluation suite."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    agent_id: uuid.UUID
    description: str | None
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EvalSuiteListResponse(BaseModel):
    """List response for evaluation suites."""

    model_config = ConfigDict(from_attributes=True)

    suites: list[EvalSuiteResponse]
    total: int


class EvalRunCreate(BaseModel):
    """Payload to initiate an evaluation run."""

    model_config = ConfigDict(extra="forbid")

    suite_id: uuid.UUID = Field(..., description="Target eval suite UUID.")
    agent_version_id: uuid.UUID | None = Field(
        default=None, description="Optional target version UUID."
    )
    trigger: str = Field(
        default="manual", description="Trigger source (manual, version_change, ci, schedule)."
    )


class EvalResultCreate(BaseModel):
    """Payload to record an individual test case evaluation result."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., max_length=100)
    case_name: str = Field(..., max_length=255)
    input_data: dict[str, Any] = Field(default_factory=dict)
    expected_output: Any | None = Field(default=None)
    actual_output: Any | None = Field(default=None)
    passed: bool = Field(...)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evaluator_name: str = Field(..., max_length=100)
    evaluator_type: str = Field(..., max_length=50)
    failure_reason: str | None = Field(default=None)
    latency_ms: int | None = Field(default=None)
    tokens_used: int | None = Field(default=None)


class EvalResultResponse(BaseModel):
    """Individual assertion result response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    eval_run_id: uuid.UUID
    case_id: str
    case_name: str
    input_data: dict[str, Any]
    expected_output: Any | None
    actual_output: Any | None
    passed: bool
    score: float
    evaluator_name: str
    evaluator_type: str
    failure_reason: str | None
    latency_ms: int | None
    tokens_used: int | None
    created_at: datetime


class EvalRunResponse(BaseModel):
    """Response representing an evaluation run execution."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    suite_id: uuid.UUID
    agent_id: uuid.UUID
    agent_version_id: uuid.UUID | None
    status: str
    trigger: str
    pass_rate: float | None
    total_cases: int
    passed_cases: int
    failed_cases: int
    duration_ms: int | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class EvalRunDetailResponse(EvalRunResponse):
    """Detailed evaluation run response with individual assertion results."""

    results: list[EvalResultResponse] = Field(default_factory=list)


class EvalRunListResponse(BaseModel):
    """List response for evaluation runs."""

    model_config = ConfigDict(from_attributes=True)

    runs: list[EvalRunResponse]
    total: int
