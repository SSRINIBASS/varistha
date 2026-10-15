"""Observability package exposing OTLP receiver, span persistence, and trace inspection."""

from __future__ import annotations

from observability.parser import ParsedSpanData, parse_otlp_payload
from observability.router import router
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

__all__ = [
    "MissingRunIdError",
    "OTLPExportResponse",
    "ParsedSpanData",
    "RunNotFoundError",
    "SpanListResponse",
    "SpanResponse",
    "TraceDetailResponse",
    "get_spans_for_run",
    "get_spans_for_trace",
    "parse_otlp_payload",
    "persist_spans",
    "router",
]
