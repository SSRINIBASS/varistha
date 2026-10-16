"""Tests validating OpenTelemetry TracerProvider initialization and OTLP exporter attachment."""

from collections.abc import Sequence

import pytest
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from shared.telemetry import (
    add_span_processor,
    get_tracer,
    init_tracer_provider,
    reset_tracer_provider,
)


class DummyExporter(SpanExporter):
    """Dummy in-memory exporter for testing."""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export dummy spans."""
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Shutdown dummy exporter."""
        pass


@pytest.fixture(autouse=True)
def _clean_tracer_provider() -> None:
    """Ensure clean tracer provider state for every test."""
    reset_tracer_provider()


def test_init_tracer_provider_default() -> None:
    """Default initialization creates a TracerProvider with correct service name."""
    provider = init_tracer_provider("test-service")
    assert isinstance(provider, TracerProvider)
    resource_attrs = provider.resource.attributes
    assert resource_attrs.get("service.name") == "test-service"


def test_init_tracer_provider_with_otlp_endpoint() -> None:
    """Explicit otlp_endpoint configures and attaches an OTLP HTTP span processor."""
    provider = init_tracer_provider(
        service_name="test-otel-service",
        otlp_endpoint="http://localhost:4318/v1/traces",
    )
    assert isinstance(provider, TracerProvider)
    # The provider should have at least one span processor registered
    assert len(provider._active_span_processor._span_processors) >= 1  # pyright: ignore[reportPrivateUsage]


def test_init_tracer_provider_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables configure OTLP endpoint and service name on provider."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    monkeypatch.setenv("OTEL_SERVICE_NAME", "custom-varistha-worker")

    provider = init_tracer_provider()
    assert isinstance(provider, TracerProvider)
    assert provider.resource.attributes.get("service.name") == "custom-varistha-worker"
    assert len(provider._active_span_processor._span_processors) >= 1  # pyright: ignore[reportPrivateUsage]


def test_get_tracer_returns_valid_tracer() -> None:
    """get_tracer initializes provider and returns a named Tracer."""
    tracer = get_tracer("test.component", "1.0.0")
    span = tracer.start_span("test-span")
    assert span.is_recording()
    span.end()


def test_add_span_processor() -> None:
    """add_span_processor successfully registers a custom processor."""
    provider = init_tracer_provider()
    dummy_proc = SimpleSpanProcessor(DummyExporter())
    add_span_processor(dummy_proc)
    assert dummy_proc in provider._active_span_processor._span_processors  # pyright: ignore[reportPrivateUsage]
