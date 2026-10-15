"""Service layer for persisting and retrieving OpenTelemetry spans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.db.models import Run, Span
from sqlalchemy import select

if TYPE_CHECKING:
    import uuid

    from observability.parser import ParsedSpanData
    from sqlalchemy.ext.asyncio import AsyncSession


class RunNotFoundError(Exception):
    """Raised when a span references a nonexistent run ID."""


class MissingRunIdError(Exception):
    """Raised when a span cannot be associated with any run ID."""


async def persist_spans(
    session: AsyncSession,
    parsed_spans: list[ParsedSpanData],
) -> list[Span]:
    """Persist parsed OTLP spans to the database."""
    if not parsed_spans:
        return []

    # Cache run_id existence checks
    verified_runs: set[uuid.UUID] = set()
    persisted: list[Span] = []

    for item in parsed_spans:
        run_id = item.run_id

        # If run_id not explicitly set, try resolving from existing spans with same trace_id
        if run_id is None:
            trace_stmt = select(Span.run_id).where(Span.trace_id == item.trace_id).limit(1)
            result = await session.execute(trace_stmt)
            existing_run_id = result.scalar_one_or_none()
            if existing_run_id:
                run_id = existing_run_id

        if run_id is None:
            raise MissingRunIdError(
                f"Span '{item.name}' (trace={item.trace_id}, span={item.span_id}) "
                "missing required varistha.run_id attribute"
            )

        if run_id not in verified_runs:
            run_stmt = select(Run).where(Run.id == run_id)
            run_result = await session.execute(run_stmt)
            if run_result.scalar_one_or_none() is None:
                raise RunNotFoundError(f"Referenced run '{run_id}' does not exist")
            verified_runs.add(run_id)

        # Check if span already exists (idempotent update)
        existing_stmt = select(Span).where(
            Span.trace_id == item.trace_id,
            Span.span_id == item.span_id,
        )
        existing_result = await session.execute(existing_stmt)
        existing_span = existing_result.scalar_one_or_none()

        if existing_span:
            existing_span.name = item.name
            existing_span.kind = item.kind
            existing_span.status = item.status
            existing_span.end_time = item.end_time
            existing_span.attributes = item.attributes
            existing_span.events = item.events
            persisted.append(existing_span)
        else:
            new_span = Span(
                run_id=run_id,
                trace_id=item.trace_id,
                span_id=item.span_id,
                parent_span_id=item.parent_span_id,
                name=item.name,
                kind=item.kind,
                start_time=item.start_time,
                end_time=item.end_time,
                status=item.status,
                attributes=item.attributes,
                events=item.events,
            )
            session.add(new_span)
            persisted.append(new_span)

    await session.commit()
    for span in persisted:
        await session.refresh(span)

    return persisted


async def get_spans_for_run(
    session: AsyncSession,
    run_id: uuid.UUID,
) -> list[Span]:
    """Retrieve all spans for a run, ordered by start time."""
    stmt = select(Span).where(Span.run_id == run_id).order_by(Span.start_time.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spans_for_trace(
    session: AsyncSession,
    trace_id: str,
) -> list[Span]:
    """Retrieve all spans for a trace, ordered by start time."""
    stmt = select(Span).where(Span.trace_id == trace_id).order_by(Span.start_time.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
