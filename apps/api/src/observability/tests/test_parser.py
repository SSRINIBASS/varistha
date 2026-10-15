"""Unit tests for OpenTelemetry OTLP JSON parser."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from observability.parser import (
    nano_to_datetime,
    normalize_id,
    normalize_kind,
    normalize_status,
    parse_attributes_list,
    parse_otlp_payload,
    parse_otlp_value,
)


def test_parse_otlp_value_unwraps_all_types() -> None:
    """Verify parse_otlp_value unwraps OpenTelemetry AnyValue structures."""
    assert parse_otlp_value({"stringValue": "hello"}) == "hello"
    assert parse_otlp_value({"intValue": "123"}) == 123
    assert parse_otlp_value({"doubleValue": "3.14"}) == 3.14
    array_val = {"arrayValue": {"values": [{"stringValue": "a"}, {"intValue": "1"}]}}
    assert parse_otlp_value(array_val) == ["a", 1]
    assert parse_otlp_value(
        {"kvlistValue": {"values": [{"key": "foo", "value": {"stringValue": "bar"}}]}}
    ) == {"foo": "bar"}
    # Raw primitive
    assert parse_otlp_value("raw_str") == "raw_str"


def test_nano_to_datetime_conversion() -> None:
    """Verify nanosecond Unix timestamp converts to UTC datetime."""
    # 1729000000 sec = 2024-10-15 13:46:40 UTC
    nano = 1729000000 * 1_000_000_000
    dt = nano_to_datetime(nano)
    assert dt is not None
    assert dt.tzinfo == UTC
    assert dt == datetime.fromtimestamp(1729000000.0, tz=UTC)

    assert nano_to_datetime(None) is None
    assert nano_to_datetime(0) is None
    assert nano_to_datetime("invalid") is None


def test_normalize_id_and_kind_and_status() -> None:
    """Verify normalization helpers for IDs, kinds, and status codes."""
    assert normalize_id("00f067aa0ba902b7") == "00f067aa0ba902b7"
    assert normalize_id("") == ""

    assert normalize_kind(1) == "INTERNAL"
    assert normalize_kind(2) == "SERVER"
    assert normalize_kind(3) == "CLIENT"
    assert normalize_kind("SPAN_KIND_PRODUCER") == "PRODUCER"

    assert normalize_status(1) == "OK"
    assert normalize_status(2) == "ERROR"
    assert normalize_status(0) == "UNSET"
    assert normalize_status({"code": 1}) == "OK"


def test_parse_attributes_list() -> None:
    """Verify attributes list parsing and dictionary fallback."""
    raw = [
        {"key": "service.name", "value": {"stringValue": "varistha"}},
        {"key": "version", "value": {"stringValue": "0.1.0"}},
    ]
    parsed = parse_attributes_list(raw)
    assert parsed == {"service.name": "varistha", "version": "0.1.0"}

    # Flat dict
    assert parse_attributes_list({"key": "val"}) == {"key": "val"}
    assert parse_attributes_list(None) == {}


def test_parse_otlp_payload_full_lifecycle() -> None:
    """Verify parsing a full OTLP JSON ExportTraceServiceRequest."""
    run_id = uuid.uuid4()
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "varistha-agent"}},
                        {"key": "varistha.run_id", "value": {"stringValue": str(run_id)}},
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "varistha.runtime", "version": "0.1.0"},
                        "spans": [
                            {
                                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                "spanId": "00f067aa0ba902b7",
                                "name": "agent.run",
                                "kind": 1,
                                "startTimeUnixNano": "1729000000000000000",
                                "endTimeUnixNano": "1729000002000000000",
                                "attributes": [
                                    {"key": "varistha.cost_usd", "value": {"doubleValue": 0.05}},
                                    {
                                        "key": "user_email",
                                        "value": {"stringValue": "user@startup.io"},
                                    },
                                    {"key": "api_key", "value": {"stringValue": "secret-123"}},
                                ],
                                "events": [
                                    {
                                        "name": "model_invoked",
                                        "timeUnixNano": "1729000001000000000",
                                        "attributes": [
                                            {"key": "model", "value": {"stringValue": "gpt-4o"}}
                                        ],
                                    }
                                ],
                                "status": {"code": 1},
                            },
                            {
                                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                "spanId": "5fb397be34d23b0f",
                                "parentSpanId": "00f067aa0ba902b7",
                                "name": "llm.call",
                                "kind": 3,
                                "startTimeUnixNano": "1729000001000000000",
                                "endTimeUnixNano": "1729000002000000000",
                                "attributes": [
                                    {"key": "gen_ai.system", "value": {"stringValue": "openai"}},
                                    {
                                        "key": "gen_ai.request.model",
                                        "value": {"stringValue": "gpt-4o"},
                                    },
                                ],
                                "status": {"code": 1},
                            },
                        ],
                    }
                ],
            }
        ]
    }

    spans = parse_otlp_payload(payload)
    assert len(spans) == 2

    root = spans[0]
    assert root.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert root.span_id == "00f067aa0ba902b7"
    assert root.parent_span_id is None
    assert root.name == "agent.run"
    assert root.kind == "INTERNAL"
    assert root.status == "OK"
    assert root.run_id == run_id
    assert root.attributes["varistha.cost_usd"] == 0.05
    assert root.attributes["user_email"] == "[REDACTED_EMAIL]"
    assert root.attributes["api_key"] == "[REDACTED_SECRET]"
    assert len(root.events) == 1
    assert root.events[0]["name"] == "model_invoked"

    child = spans[1]
    assert child.span_id == "5fb397be34d23b0f"
    assert child.parent_span_id == "00f067aa0ba902b7"
    assert child.name == "llm.call"
    assert child.kind == "CLIENT"
    assert child.run_id == run_id


def test_parse_otlp_payload_empty_and_fallback_run_id() -> None:
    """Verify empty payload handling and fallback_run_id parameter."""
    assert parse_otlp_payload({}) == []
    assert parse_otlp_payload({"resourceSpans": "not-a-list"}) == []

    fallback_id = uuid.uuid4()
    minimal_payload = {
        "spans": [
            {
                "traceId": "11112222333344445555666677778888",
                "spanId": "1111222233334444",
                "name": "simple-span",
            }
        ]
    }
    parsed = parse_otlp_payload(minimal_payload, fallback_run_id=str(fallback_id))
    assert len(parsed) == 1
    assert parsed[0].run_id == fallback_id
    assert parsed[0].name == "simple-span"
