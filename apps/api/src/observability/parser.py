"""Parser for OpenTelemetry OTLP JSON trace export payloads."""

from __future__ import annotations

import base64
import binascii
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.telemetry.conventions import VARISTHA_RUN_ID
from shared.telemetry.redaction import redact_attributes

_KIND_MAP: dict[int, str] = {
    0: "SPAN_KIND_UNSPECIFIED",
    1: "INTERNAL",
    2: "SERVER",
    3: "CLIENT",
    4: "PRODUCER",
    5: "CONSUMER",
}

_STATUS_MAP: dict[int, str] = {
    0: "UNSET",
    1: "OK",
    2: "ERROR",
}


@dataclass
class ParsedSpanData:
    """Normalized span attributes ready for database insertion."""

    trace_id: str
    span_id: str
    name: str
    start_time: datetime
    run_id: uuid.UUID | None = None
    parent_span_id: str | None = None
    kind: str = "INTERNAL"
    end_time: datetime | None = None
    status: str = "UNSET"
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


def parse_otlp_value(val: Any) -> Any:
    """Unwrap standard OpenTelemetry AnyValue structures."""
    if not isinstance(val, dict):
        return val

    # OpenTelemetry AnyValue schema
    if "stringValue" in val:
        return val["stringValue"]
    if "intValue" in val:
        try:
            return int(val["intValue"])
        except (ValueError, TypeError):
            return val["intValue"]
    if "doubleValue" in val:
        try:
            return float(val["doubleValue"])
        except (ValueError, TypeError):
            return val["doubleValue"]
    if "boolValue" in val:
        return bool(val["boolValue"])
    if "arrayValue" in val:
        values = val["arrayValue"].get("values", [])
        return [parse_otlp_value(v) for v in values]
    if "kvlistValue" in val:
        values = val["kvlistValue"].get("values", [])
        return {
            item["key"]: parse_otlp_value(item.get("value")) for item in values if "key" in item
        }

    # Already a standard dictionary
    return {k: parse_otlp_value(v) for k, v in val.items()}


def parse_attributes_list(raw_attrs: Any) -> dict[str, Any]:
    """Parse list of OpenTelemetry KeyValue pairs or flat dictionary."""
    if not raw_attrs:
        return {}

    if isinstance(raw_attrs, dict):
        return {str(k): parse_otlp_value(v) for k, v in raw_attrs.items()}

    attrs: dict[str, Any] = {}
    if isinstance(raw_attrs, list):
        for item in raw_attrs:
            if isinstance(item, dict) and "key" in item:
                attrs[str(item["key"])] = parse_otlp_value(item.get("value"))
    return attrs


def normalize_id(raw_id: Any) -> str:
    """Normalize trace_id or span_id from hex string or base64."""
    if not raw_id:
        return ""
    val_str = str(raw_id).strip()

    # If it is valid hex string (e.g. 16 or 32 characters)
    try:
        binascii.unhexlify(val_str)
        return val_str.lower()
    except binascii.Error:
        pass

    # Try base64 decoding to hex
    try:
        raw_bytes = base64.b64decode(val_str)
        return raw_bytes.hex().lower()
    except Exception:
        return val_str.lower()


def nano_to_datetime(nano_val: Any) -> datetime | None:
    """Convert Unix nanosecond timestamp to timezone-aware UTC datetime."""
    if nano_val is None:
        return None
    try:
        nano_int = int(nano_val)
        if nano_int <= 0:
            return None
        timestamp_sec = nano_int / 1_000_000_000.0
        return datetime.fromtimestamp(timestamp_sec, tz=UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def normalize_kind(raw_kind: Any) -> str:
    """Normalize OTel span kind integer or string representation."""
    if isinstance(raw_kind, int):
        return _KIND_MAP.get(raw_kind, "INTERNAL")
    if isinstance(raw_kind, str):
        upper = raw_kind.upper()
        if upper.startswith("SPAN_KIND_"):
            return upper.replace("SPAN_KIND_", "")
        return upper
    return "INTERNAL"


def normalize_status(raw_status: Any) -> str:
    """Normalize OTel span status object or code."""
    if isinstance(raw_status, dict):
        code = raw_status.get("code")
        if isinstance(code, int):
            return _STATUS_MAP.get(code, "UNSET")
        if isinstance(code, str):
            return code.upper().replace("STATUS_CODE_", "")
    if isinstance(raw_status, int):
        return _STATUS_MAP.get(raw_status, "UNSET")
    if isinstance(raw_status, str):
        return raw_status.upper()
    return "UNSET"


def extract_run_id(
    span_attrs: dict[str, Any],
    resource_attrs: dict[str, Any],
    fallback_run_id: str | None = None,
) -> uuid.UUID | None:
    """Extract and validate run_id from span or resource attributes."""
    candidate = (
        span_attrs.get(VARISTHA_RUN_ID)
        or span_attrs.get("run_id")
        or resource_attrs.get(VARISTHA_RUN_ID)
        or resource_attrs.get("run_id")
        or fallback_run_id
    )
    if candidate:
        try:
            return uuid.UUID(str(candidate))
        except (ValueError, AttributeError):
            return None
    return None


def parse_otlp_payload(
    payload: dict[str, Any],
    fallback_run_id: str | None = None,
) -> list[ParsedSpanData]:
    """Parse complete OTLP JSON export into a list of ParsedSpanData."""
    results: list[ParsedSpanData] = []

    # Handle standard OTLP HTTP JSON payload format
    resource_spans = payload.get("resourceSpans") or payload.get("resource_spans")

    # Fallback to direct spans list if passed directly
    if resource_spans is None and "spans" in payload:
        spans_list = payload.get("spans", [])
        resource_spans = [{"scopeSpans": [{"spans": spans_list}]}]

    if not isinstance(resource_spans, list):
        return results

    for r_span in resource_spans:
        if not isinstance(r_span, dict):
            continue

        raw_resource = r_span.get("resource")
        resource_attrs = (
            parse_attributes_list(raw_resource.get("attributes"))
            if isinstance(raw_resource, dict)
            else {}
        )

        scope_spans = r_span.get("scopeSpans") or r_span.get("scope_spans") or []
        if not isinstance(scope_spans, list):
            continue

        for s_span in scope_spans:
            if not isinstance(s_span, dict):
                continue

            spans = s_span.get("spans", [])
            if not isinstance(spans, list):
                continue

            for span in spans:
                if not isinstance(span, dict):
                    continue

                trace_id = normalize_id(span.get("traceId") or span.get("trace_id"))
                span_id = normalize_id(span.get("spanId") or span.get("span_id"))
                raw_parent = span.get("parentSpanId") or span.get("parent_span_id")
                parent_span_id = normalize_id(raw_parent) if raw_parent else None

                if not trace_id or not span_id:
                    continue

                name = str(span.get("name", "unnamed-span"))
                kind = normalize_kind(span.get("kind"))

                raw_start = span.get("startTimeUnixNano") or span.get("start_time_unix_nano")
                start_time = nano_to_datetime(raw_start) or datetime.now(UTC)
                end_time = nano_to_datetime(
                    span.get("endTimeUnixNano") or span.get("end_time_unix_nano")
                )

                status = normalize_status(span.get("status"))

                raw_attrs = parse_attributes_list(span.get("attributes"))
                merged_attrs = {**resource_attrs, **raw_attrs}
                redacted_attrs = redact_attributes(merged_attrs)

                # Parse events if present
                raw_events = span.get("events", [])
                parsed_events: list[dict[str, Any]] = []
                if isinstance(raw_events, list):
                    for event in raw_events:
                        if isinstance(event, dict):
                            parsed_events.append(
                                {
                                    "name": event.get("name", ""),
                                    "time": (
                                        nano_to_datetime(
                                            event.get("timeUnixNano") or event.get("time_unix_nano")
                                        )
                                        or datetime.now(UTC)
                                    ).isoformat(),
                                    "attributes": redact_attributes(
                                        parse_attributes_list(event.get("attributes"))
                                    ),
                                }
                            )

                run_id = extract_run_id(
                    span_attrs=raw_attrs,
                    resource_attrs=resource_attrs,
                    fallback_run_id=fallback_run_id,
                )

                results.append(
                    ParsedSpanData(
                        trace_id=trace_id,
                        span_id=span_id,
                        parent_span_id=parent_span_id,
                        name=name,
                        kind=kind,
                        start_time=start_time,
                        end_time=end_time,
                        status=status,
                        attributes=redacted_attrs,
                        events=parsed_events,
                        run_id=run_id,
                    )
                )

    return results
