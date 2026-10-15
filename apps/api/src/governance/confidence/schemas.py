"""Pydantic schemas for review-priority and confidence scoring."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConfidenceSignal(BaseModel):
    """An individual verifiable confidence signal."""

    name: str = Field(..., description="Signal identifier.")
    weight: float = Field(..., ge=0.0, le=1.0, description="Signal contribution weight.")
    score: float = Field(..., ge=0.0, le=1.0, description="Evaluated score for this signal.")
    passed: bool = Field(..., description="Whether signal reached required threshold.")
    details: str = Field(..., description="Human-readable explanation of signal calculation.")


class ConfidenceEvaluationRequest(BaseModel):
    """Input payload to evaluate review-priority and confidence."""

    agent_id: str = Field(..., description="Target agent UUID.")
    version_id: str | None = Field(default=None, description="Optional target version UUID.")
    output: Any = Field(..., description="Candidate agent output to evaluate.")
    input_context: Any | None = Field(
        default=None, description="Input payload or source context for grounding."
    )
    schema_def: dict[str, Any] | None = Field(
        default=None, description="Expected JSON Schema if structured output."
    )


class ReviewPriorityOutcome(BaseModel):
    """Review-priority score and breakdown derived from verifiable signals."""

    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Aggregate confidence score (0.0 to 1.0)."
    )
    review_priority: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description=(
            "Review-priority: low (>=0.8), medium (0.6-0.8), high (0.4-0.6), critical (<0.4)."
        ),
    )
    signals: list[ConfidenceSignal] = Field(
        default_factory=list, description="Verifiable signal breakdown."
    )
    rationale: str = Field(
        ..., description="Human-readable justification for the review-priority level."
    )
