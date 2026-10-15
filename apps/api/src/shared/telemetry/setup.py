"""OpenTelemetry tracer provider initialization and management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import SpanProcessor
    from opentelemetry.trace import Tracer

_provider_initialized = False


def init_tracer_provider(service_name: str = "varistha-api") -> TracerProvider:
    """Initialize and register the global TracerProvider if not already set."""
    global _provider_initialized

    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider) and _provider_initialized:
        return current_provider

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
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
