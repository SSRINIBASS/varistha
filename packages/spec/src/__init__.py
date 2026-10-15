"""Public API for the varistha-spec package.

Exports:
    AgentSpec           - Top-level typed spec model
    AgentMetadata       - Metadata block (name, owner, stage, version)
    AgentSpecBody       - Spec body (role, model, plugins, autonomy, etc.)
    ModelConfig         - Primary/fallback model config
    PluginRef           - Plugin toggle reference
    GuardrailsConfig    - Input/output/tool guardrail lists
    BudgetConfig        - Per-run and per-day USD limits
    TriggerConfig       - Schedule/webhook/manual trigger
    EvalConfig          - Eval suite reference and min pass rate
    SpecValidationError - Raised on validation failure
    validate_spec       - Validate a raw dict -> AgentSpec
    validate_spec_yaml  - Validate a YAML string -> AgentSpec
    generate_json_schema - Return JSON Schema dict for AgentSpec
    diff_specs          - Compare two specs and detect breaking changes
    SpecDiff            - Structured diff summary model
    DiffEntry           - Detailed field-level diff entry model
    ChangeType          - Added, removed, or modified change type enum
"""

from diff import ChangeType, DiffEntry, SpecDiff, diff_specs
from exceptions import SpecValidationError
from models import (
    AgentMetadata,
    AgentSpec,
    AgentSpecBody,
    BudgetConfig,
    EvalConfig,
    GuardrailsConfig,
    ModelConfig,
    PluginRef,
    TriggerConfig,
)
from schema import generate_json_schema
from validator import validate_spec, validate_spec_yaml

__all__ = [
    "AgentMetadata",
    "AgentSpec",
    "AgentSpecBody",
    "BudgetConfig",
    "ChangeType",
    "DiffEntry",
    "EvalConfig",
    "GuardrailsConfig",
    "ModelConfig",
    "PluginRef",
    "SpecDiff",
    "SpecValidationError",
    "TriggerConfig",
    "diff_specs",
    "generate_json_schema",
    "validate_spec",
    "validate_spec_yaml",
]
