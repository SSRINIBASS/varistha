"""OpenTelemetry tracer provider initialization and management."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import SpanProcessor
    from opentelemetry.trace import Tracer

logger = logging.getLogger(__name__)

_provider_initialized = False


def reset_tracer_provider() -> None:
    """Reset the global TracerProvider (primarily for test harnesses)."""
    global _provider_initialized
    _provider_initialized = False
    trace._TRACER_PROVIDER = None  # pyright: ignore[reportPrivateUsage]
    once = getattr(trace, "_TRACER_PROVIDER_SET_ONCE", None)
    if once is not None and hasattr(once, "_done"):
        once._done = False  # pyright: ignore[reportPrivateUsage]


def init_tracer_provider(
    service_name: str | None = None,
    otlp_endpoint: str | None = None,
) -> TracerProvider:
    """Initialize and register the global TracerProvider if not already set."""
    global _provider_initialized

    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider) and _provider_initialized:
        return current_provider

    effective_service_name = service_name or os.getenv("OTEL_SERVICE_NAME") or "varistha-api"

    resource = Resource.create({"service.name": effective_service_name})
    provider = TracerProvider(resource=resource)

    # Attach OTLP HTTP SpanExporter if an endpoint is configured
    effective_endpoint = (
        otlp_endpoint
        if otlp_endpoint is not None
        else os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    )

    if effective_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = OTLPSpanExporter(endpoint=effective_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("Configured OTLP HTTP trace exporter to %s", effective_endpoint)
        except Exception as exc:
            logger.warning(
                "Failed to initialize OTLP HTTP trace exporter for %s: %s",
                effective_endpoint,
                exc,
            )

    trace.set_tracer_provider(provider)
    _provider_initialized = True
    return provider


def get_tracer(name: str = "varistha", version: str = "0.1.0") -> Tracer:
    """Return an OpenTelemetry tracer for the given instrumented component."""
    init_tracer_provider()
    return trace.get_tracer(name, version)


def add_span_processor(processor: SpanProcessor) -> None:
    """Add a span processor to the global TracerProvider."""
    provider = init_tracer_provider()
    provider.add_span_processor(processor)
