"""Pydantic schemas for observability, traces, and spans."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpanResponse(BaseModel):
    """Execution span representation for traces and waterfall visualization."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    name: str
    kind: str
    start_time: datetime
    end_time: datetime | None = None
    status: str
    attributes: dict[str, Any] | None = None
    events: list[dict[str, Any]] | None = None
    duration_ms: float | None = None


class SpanListResponse(BaseModel):
    """Response containing ordered list of spans for a run."""

    items: list[SpanResponse]
    total: int


class TraceDetailResponse(BaseModel):
    """Detailed view of an entire trace across its spans."""

    trace_id: str
    run_id: uuid.UUID | None = None
    total_spans: int
    root_span: SpanResponse | None = None
    spans: list[SpanResponse]


class OTLPExportResponse(BaseModel):
    """Standard response model for OTLP HTTP trace exports."""

    model_config = ConfigDict(populate_by_name=True)

    partial_success: dict[str, Any] = Field(
        default_factory=dict,
        serialization_alias="partialSuccess",
    )
