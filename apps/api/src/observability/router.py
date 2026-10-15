"""FastAPI router for OTLP trace ingestion and span inspection."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from observability.parser import parse_otlp_payload
from observability.schemas import (
    OTLPExportResponse,
    SpanListResponse,
    SpanResponse,
    TraceDetailResponse,
)
from observability.service import (
    MissingRunIdError,
    RunNotFoundError,
    get_spans_for_run,
    get_spans_for_trace,
    persist_spans,
)
from shared.db.session import get_db_session

if TYPE_CHECKING:
    from shared.db.models import Span
    from sqlalchemy.ext.asyncio import AsyncSession

DbSession = Annotated["AsyncSession", Depends(get_db_session)]

router = APIRouter(tags=["observability"])


def _calculate_duration_ms(span: Span) -> float | None:
    """Calculate span duration in milliseconds if end_time is available."""
    if span.end_time and span.start_time:
        delta = (span.end_time - span.start_time).total_seconds()
        return round(delta * 1000.0, 3)
    return None


def _span_to_response(span: Span) -> SpanResponse:
    """Convert database Span model to API SpanResponse schema."""
    return SpanResponse(
        id=span.id,
        run_id=span.run_id,
        trace_id=span.trace_id,
        span_id=span.span_id,
        parent_span_id=span.parent_span_id,
        name=span.name,
        kind=span.kind,
        start_time=span.start_time,
        end_time=span.end_time,
        status=span.status,
        attributes=span.attributes or {},
        events=span.events or [],
        duration_ms=_calculate_duration_ms(span),
    )


@router.post(
    "/v1/traces",
    response_model=OTLPExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Standard OTLP HTTP trace receiver",
)
@router.post(
    "/api/v1/traces",
    response_model=OTLPExportResponse,
    status_code=status.HTTP_200_OK,
    summary="API alias for OTLP HTTP trace receiver",
)
async def ingest_otlp_traces(
    request: Request,
    run_id: str | None = Query(None, description="Optional fallback run ID"),
    x_varistha_run_id: str | None = Header(None, alias="X-Varistha-Run-Id"),
    session: DbSession = None,  # type: ignore[assignment]
) -> OTLPExportResponse:
    """Receive and persist OpenTelemetry OTLP JSON traces."""
    try:
        body: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {exc}",
        ) from exc

    fallback = x_varistha_run_id or run_id
    parsed = parse_otlp_payload(body, fallback_run_id=fallback)

    try:
        await persist_spans(session, parsed)
    except MissingRunIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return OTLPExportResponse()


@router.get(
    "/api/v1/runs/{run_id}/spans",
    response_model=SpanListResponse,
    summary="List all spans for an agent run",
)
async def list_spans_for_run(
    run_id: str,
    session: DbSession = None,  # type: ignore[assignment]
) -> SpanListResponse:
    """Retrieve all spans belonging to a run in chronological order."""
    try:
        run_uuid = uuid.UUID(run_id)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID: '{run_id}'",
        ) from exc

    spans = await get_spans_for_run(session, run_uuid)
    items = [_span_to_response(s) for s in spans]
    return SpanListResponse(items=items, total=len(items))


@router.get(
    "/api/v1/traces/{trace_id}",
    response_model=TraceDetailResponse,
    summary="Get trace details across all spans",
)
async def get_trace_detail(
    trace_id: str,
    session: DbSession = None,  # type: ignore[assignment]
) -> TraceDetailResponse:
    """Retrieve all spans matching a trace ID."""
    clean_trace_id = trace_id.strip().lower()
    spans = await get_spans_for_trace(session, clean_trace_id)

    if not spans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace '{clean_trace_id}' not found",
        )

    items = [_span_to_response(s) for s in spans]
    root_span = next((s for s in items if s.parent_span_id is None), None)
    run_id = spans[0].run_id if spans else None

    return TraceDetailResponse(
        trace_id=clean_trace_id,
        run_id=run_id,
        total_spans=len(items),
        root_span=root_span,
        spans=items,
    )
