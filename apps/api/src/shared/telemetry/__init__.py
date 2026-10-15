"""Shared telemetry kernel module."""

from __future__ import annotations

from shared.telemetry.conventions import (
    GEN_AI_OUTPUT_TYPE,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_SYSTEM,
    GEN_AI_USAGE_COMPLETION_TOKENS,
    GEN_AI_USAGE_PROMPT_TOKENS,
    GEN_AI_USAGE_TOTAL_TOKENS,
    VARISTHA_AGENT_ID,
    VARISTHA_AGENT_NAME,
    VARISTHA_AGENT_VERSION,
    VARISTHA_APPROVAL_REQUIRED,
    VARISTHA_APPROVAL_STATUS,
    VARISTHA_AUTONOMY,
    VARISTHA_BUDGET_EXCEEDED,
    VARISTHA_COST_USD,
    VARISTHA_KILL_SWITCH_TRIPPED,
    VARISTHA_RUN_ID,
    VARISTHA_STAGE,
    VARISTHA_TRIGGER_TYPE,
)
from shared.telemetry.recorder import (
    capture_run_spans,
    save_captured_spans,
    span_to_db_model,
)
from shared.telemetry.redaction import redact_attributes, redact_string, redact_value
from shared.telemetry.setup import add_span_processor, get_tracer, init_tracer_provider

__all__ = [
    "GEN_AI_OUTPUT_TYPE",
    "GEN_AI_REQUEST_MODEL",
    "GEN_AI_SYSTEM",
    "GEN_AI_USAGE_COMPLETION_TOKENS",
    "GEN_AI_USAGE_PROMPT_TOKENS",
    "GEN_AI_USAGE_TOTAL_TOKENS",
    "VARISTHA_AGENT_ID",
    "VARISTHA_AGENT_NAME",
    "VARISTHA_AGENT_VERSION",
    "VARISTHA_APPROVAL_REQUIRED",
    "VARISTHA_APPROVAL_STATUS",
    "VARISTHA_AUTONOMY",
    "VARISTHA_BUDGET_EXCEEDED",
    "VARISTHA_COST_USD",
    "VARISTHA_KILL_SWITCH_TRIPPED",
    "VARISTHA_RUN_ID",
    "VARISTHA_STAGE",
    "VARISTHA_TRIGGER_TYPE",
    "add_span_processor",
    "capture_run_spans",
    "get_tracer",
    "init_tracer_provider",
    "redact_attributes",
    "redact_string",
    "redact_value",
    "save_captured_spans",
    "span_to_db_model",
]
