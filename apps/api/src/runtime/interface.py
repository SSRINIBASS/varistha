"""Runtime protocol and data models for AI agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import uuid


@dataclass(frozen=True)
class RunContext:
    """Execution context provided to the runtime engine."""

    run_id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: str
    model: str
    instructions: str
    input_data: dict[str, Any] = field(default_factory=dict)
    spec_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunResult:
    """Outcome of an agent execution."""

    status: str  # "completed", "failed", "waiting_approval"
    output: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    total_tokens: int = 0
    error: str | None = None


@runtime_checkable
class Runtime(Protocol):
    """Abstract protocol for agent execution engines."""

    async def execute(self, context: RunContext) -> RunResult:
        """Execute an agent within the given run context."""
        ...
