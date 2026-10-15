"""Context-aware OpenTelemetry span recording and database persistence."""

from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from shared.db.models import Span
from shared.telemetry.conventions import VARISTHA_RUN_ID
from shared.telemetry.redaction import redact_attributes
from shared.telemetry.setup import add_span_processor

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.ext.asyncio import AsyncSession

# Context variable to capture spans emitted during a specific run
_CURRENT_RUN_ID: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "current_run_id", default=None
)
_RUN_SPANS_BUFFER: contextvars.ContextVar[list[ReadableSpan] | None] = contextvars.ContextVar(
    "run_spans_buffer", default=None
)


class RunSpanProcessor(SpanProcessor):
    """OpenTelemetry span processor that captures spans into active run buffers."""

    def on_start(self, span: Any, parent_context: Any = None) -> None:
        """Inject active varistha.run_id attribute on span creation if available."""
        current_run_id = _CURRENT_RUN_ID.get()
        if current_run_id is not None:
            span.set_attribute(VARISTHA_RUN_ID, str(current_run_id))

    def on_end(self, span: ReadableSpan) -> None:
        """Store finished span into the active run buffer."""
        buffer = _RUN_SPANS_BUFFER.get()
        if buffer is not None:
            buffer.append(span)

    def shutdown(self) -> None:
        """Shutdown processor."""

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Flush processor."""
        return True


# Register processor once globally
_processor = RunSpanProcessor()
add_span_processor(_processor)


@contextmanager
def capture_run_spans(run_id: uuid.UUID) -> Generator[list[ReadableSpan], None, None]:
    """Capture all OpenTelemetry spans created within this context block for the run."""
    buffer: list[ReadableSpan] = []
    token_run = _CURRENT_RUN_ID.set(run_id)
    token_buf = _RUN_SPANS_BUFFER.set(buffer)
    try:
        yield buffer
    finally:
        _CURRENT_RUN_ID.reset(token_run)
        _RUN_SPANS_BUFFER.reset(token_buf)


def nano_to_utc_datetime(nano_timestamp: int | None) -> datetime:
    """Convert nanoseconds to timezone-aware UTC datetime."""
    if nano_timestamp is None or nano_timestamp <= 0:
        return datetime.now(UTC)
    return datetime.fromtimestamp(nano_timestamp / 1_000_000_000.0, tz=UTC)


def span_to_db_model(span: ReadableSpan, default_run_id: uuid.UUID) -> Span:
    """Convert an OpenTelemetry ReadableSpan into a database Span model."""
    span_ctx = span.get_span_context()
    trace_id = f"{span_ctx.trace_id:032x}" if span_ctx is not None else ""
    span_id = f"{span_ctx.span_id:016x}" if span_ctx is not None else ""
    parent_span_id = f"{span.parent.span_id:016x}" if span.parent is not None else None

    # Determine run_id from span attributes or fallback to default
    raw_run_id = span.attributes.get(VARISTHA_RUN_ID) if span.attributes else None
    run_id = default_run_id
    if raw_run_id:
        try:
            run_id = uuid.UUID(str(raw_run_id))
        except (ValueError, AttributeError):
            run_id = default_run_id

    # Parse events
    events_data: list[dict[str, Any]] = []
    if span.events:
        for ev in span.events:
            events_data.append(
                {
                    "name": ev.name,
                    "time": nano_to_utc_datetime(ev.timestamp).isoformat(),
                    "attributes": redact_attributes(dict(ev.attributes or {})),
                }
            )

    raw_attrs = dict(span.attributes or {})
    redacted_attrs = redact_attributes(raw_attrs)

    start_time = nano_to_utc_datetime(span.start_time)
    end_time = nano_to_utc_datetime(span.end_time) if span.end_time else None

    return Span(
        run_id=run_id,
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        name=span.name,
        kind=span.kind.name,
        start_time=start_time,
        end_time=end_time,
        status=span.status.status_code.name,
        attributes=redacted_attrs,
        events=events_data,
    )


async def save_captured_spans(
    session: AsyncSession,
    captured_spans: list[ReadableSpan],
    default_run_id: uuid.UUID,
) -> list[Span]:
    """Convert and persist captured OpenTelemetry spans to the database."""
    if not captured_spans:
        return []

    db_spans = [span_to_db_model(s, default_run_id) for s in captured_spans]
    session.add_all(db_spans)
    await session.flush()
    return db_spans
