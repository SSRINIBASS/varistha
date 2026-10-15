"""Interface definitions for guardrails and policies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class PolicyHook(StrEnum):
    """Guardrail execution hook points matching AgentSpec guardrails fields."""

    INPUT = "input"
    OUTPUT = "output"
    TOOL_CALL = "tools"


class PolicyAction(StrEnum):
    """Action outcome from a guardrail evaluation."""

    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"


class PolicyResult(BaseModel):
    """Result of evaluating a guardrail policy."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    passed: bool = Field(..., description="Whether the payload passed the guardrail.")
    action: str = Field(
        default=PolicyAction.ALLOW.value,
        description="Outcome action: allow, redact, or block.",
    )
    modified_data: Any | None = Field(
        default=None,
        description="Sanitized, transformed, or redacted payload if action is redact.",
    )
    violations: list[str] = Field(
        default_factory=list,
        description="Explanatory descriptions of detected violations.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetry, statistics, or audit details.",
    )


class PolicyContext(BaseModel):
    """Contextual metadata supplied to policy evaluators."""

    agent_id: str | None = Field(default=None, description="ID of agent under evaluation.")
    agent_name: str | None = Field(default=None, description="Name slug of agent.")
    hook: PolicyHook = Field(..., description="Active evaluation hook.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary execution context."
    )


class BasePolicy(ABC):
    """Abstract base class for all guardrail policies."""

    name: str
    description: str
    supported_hooks: ClassVar[set[PolicyHook]]

    @abstractmethod
    async def evaluate(self, data: Any, context: PolicyContext) -> PolicyResult:
        """Evaluate input, output, or tool payload and return PolicyResult."""
        raise NotImplementedError
