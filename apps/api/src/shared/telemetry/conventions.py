"""OpenTelemetry GenAI and Varistha semantic conventions."""

from __future__ import annotations

# Varistha namespace attributes
VARISTHA_RUN_ID = "varistha.run_id"
VARISTHA_AGENT_ID = "varistha.agent_id"
VARISTHA_AGENT_NAME = "varistha.agent_name"
VARISTHA_AGENT_VERSION = "varistha.agent_version"
VARISTHA_STAGE = "varistha.stage"
VARISTHA_AUTONOMY = "varistha.autonomy"
VARISTHA_COST_USD = "varistha.cost_usd"
VARISTHA_TRIGGER_TYPE = "varistha.trigger_type"
VARISTHA_APPROVAL_REQUIRED = "varistha.approval_required"
VARISTHA_APPROVAL_STATUS = "varistha.approval_status"
VARISTHA_BUDGET_EXCEEDED = "varistha.budget.exceeded"
VARISTHA_KILL_SWITCH_TRIPPED = "varistha.kill_switch_tripped"

# OpenTelemetry GenAI semantic conventions
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_USAGE_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
GEN_AI_USAGE_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
GEN_AI_USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
GEN_AI_OUTPUT_TYPE = "gen_ai.output.type"
