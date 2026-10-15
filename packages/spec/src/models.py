"""Pydantic v2 models for the Varistha Agent Spec.

These models represent the canonical ``varistha/v1 Agent`` specification
described in docs/SPEC.md § 3.4.  All models are strict (``extra="forbid"``)
so unknown fields cause a hard validation failure rather than silent discard.

The ``instructions`` field accepts either a relative file path or inline text.
Path existence is intentionally *not* checked here — that is a runtime concern.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?(\+[A-Za-z0-9.]+)?$")
_CRON_FIELDS = 5  # space-separated fields in a cron expression


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class AgentMetadata(BaseModel):
    """Metadata block: identity, ownership, and lifecycle stage."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Unique slug identifier for the agent. Must match [a-z0-9][a-z0-9-]*.",
    )
    owner: EmailStr = Field(..., description="E-mail address of the agent owner.")
    stage: Literal["draft", "prototype", "staging", "production", "deprecated", "retired"] = Field(
        ...,
        description="Lifecycle stage of the agent.",
    )
    version: str = Field(
        ...,
        description="Semantic version string (e.g. 0.3.0).",
    )

    @field_validator("name")
    @classmethod
    def name_must_be_slug(cls, value: str) -> str:
        """Enforce lowercase slug format for agent names."""
        if not _SLUG_RE.match(value):
            msg = (
                f"'{value}' is not a valid agent name. "
                "Must match [a-z0-9][a-z0-9-]* (lowercase letters, digits, hyphens only, "
                "must start with a letter or digit)."
            )
            raise ValueError(msg)
        return value

    @field_validator("version")
    @classmethod
    def version_must_be_semver(cls, value: str) -> str:
        """Enforce semver-compatible version strings."""
        if not _SEMVER_RE.match(value):
            msg = f"'{value}' is not a valid version. Expected MAJOR.MINOR.PATCH (e.g. 0.3.0)."
            raise ValueError(msg)
        return value


class ModelConfig(BaseModel):
    """Model selection config: primary model and optional fallback."""

    model_config = ConfigDict(extra="forbid")

    primary: str = Field(
        ...,
        min_length=1,
        description="LiteLLM model identifier (e.g. gpt-4o, ollama/llama3).",
    )
    fallback: str | None = Field(
        default=None,
        description="Optional fallback LiteLLM model identifier.",
    )


class PluginRef(BaseModel):
    """A plugin toggle within an agent spec."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Plugin name as declared in its manifest.")
    enabled: bool = Field(..., description="Whether the plugin is active for this agent.")


class GuardrailsConfig(BaseModel):
    """Guardrail policy lists for input, output, and tool calls."""

    model_config = ConfigDict(extra="forbid")

    input: list[str] = Field(default_factory=list, description="Input guardrail policy names.")
    output: list[str] = Field(default_factory=list, description="Output guardrail policy names.")
    tools: list[str] = Field(default_factory=list, description="Tool-call guardrail policy names.")


class BudgetConfig(BaseModel):
    """Per-run and per-day USD spend limits."""

    model_config = ConfigDict(extra="forbid")

    max_usd_per_run: Annotated[float, Field(gt=0)] = Field(
        ...,
        description="Maximum USD cost allowed per single run.",
    )
    max_usd_per_day: Annotated[float, Field(gt=0)] = Field(
        ...,
        description="Maximum USD cost allowed across all runs in a calendar day.",
    )


class TriggerConfig(BaseModel):
    """A run trigger: schedule (cron), webhook, or manual."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["schedule", "webhook", "manual"] = Field(
        ...,
        description="Trigger mechanism.",
    )
    cron: str | None = Field(
        default=None,
        description="Cron expression (required when type=schedule). 5-field POSIX format.",
    )

    @model_validator(mode="after")
    def cron_required_for_schedule(self) -> TriggerConfig:
        """Require a cron expression when trigger type is 'schedule'."""
        if self.type == "schedule" and not self.cron:
            msg = "A 'cron' expression is required when trigger type is 'schedule'."
            raise ValueError(msg)
        if self.cron is not None:
            parts = self.cron.split()
            if len(parts) != _CRON_FIELDS:
                msg = (
                    f"Invalid cron expression '{self.cron}'. "
                    f"Expected 5 space-separated fields, got {len(parts)}."
                )
                raise ValueError(msg)
        return self


class EvalConfig(BaseModel):
    """Evaluation suite reference and minimum pass-rate gate."""

    model_config = ConfigDict(extra="forbid")

    suite: str = Field(
        ...,
        min_length=1,
        description="Path or identifier of the evaluation suite YAML.",
    )
    min_pass_rate: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ...,
        description="Minimum fraction of eval cases that must pass (0.0-1.0).",
    )


class AgentSpecBody(BaseModel):
    """The 'spec' block: runtime behaviour, plugins, guardrails, budget, triggers, evals."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(
        ...,
        min_length=1,
        description="Plain-language description of what this agent does.",
    )
    model: ModelConfig = Field(..., description="Primary and fallback model configuration.")
    instructions: str = Field(
        ...,
        min_length=1,
        description=(
            "Relative file path to a prompt/instructions file OR inline instruction text. "
            "File existence is validated at runtime, not at parse time."
        ),
    )
    plugins: list[PluginRef] = Field(
        default_factory=list,
        description="Plugin toggles available to this agent.",
    )
    autonomy: Literal["L0", "L1", "L2", "L3"] = Field(
        ...,
        description=(
            "Autonomy level. L0=suggest only, L1=act with approval, "
            "L2=act with sampled review, L3=autonomous within budget."
        ),
    )
    guardrails: GuardrailsConfig | None = Field(
        default=None,
        description="Optional guardrail policy configuration.",
    )
    budget: BudgetConfig | None = Field(
        default=None,
        description="Optional per-run and per-day USD spend limits.",
    )
    triggers: list[TriggerConfig] = Field(
        default_factory=list,
        description="One or more triggers that can start a run.",
    )
    evals: EvalConfig | None = Field(
        default=None,
        description="Optional evaluation suite and minimum pass-rate gate.",
    )


# ---------------------------------------------------------------------------
# Top-level spec
# ---------------------------------------------------------------------------


class AgentSpec(BaseModel):
    """Top-level Varistha agent specification (apiVersion: varistha/v1, kind: Agent)."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Literal["varistha/v1"] = Field(  # noqa: N815 — matches YAML key
        ...,
        description="Must be 'varistha/v1'.",
    )
    kind: Literal["Agent"] = Field(..., description="Must be 'Agent'.")
    metadata: AgentMetadata
    spec: AgentSpecBody
