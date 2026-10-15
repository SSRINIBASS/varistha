"""Mock runtime implementation for testing and offline development."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from runtime.interface import RunResult
from shared.telemetry import (
    GEN_AI_REQUEST_MODEL,
    GEN_AI_SYSTEM,
    GEN_AI_USAGE_TOTAL_TOKENS,
    VARISTHA_COST_USD,
    get_tracer,
)

if TYPE_CHECKING:
    from runtime.interface import RunContext


class MockRuntime:
    """Deterministic mock runtime for tests and development without LLM API keys."""

    def __init__(
        self,
        default_output: dict[str, Any] | None = None,
        should_fail: bool = False,
        error_message: str = "Simulated mock failure",
        waiting_approval: bool = False,
        tokens: int = 150,
        cost_usd: float = 0.0025,
    ) -> None:
        """Initialize mock runtime with configurable behavior."""
        self.default_output = default_output
        self.should_fail = should_fail
        self.error_message = error_message
        self.waiting_approval = waiting_approval
        self.tokens = tokens
        self.cost_usd = cost_usd
        self.executed_contexts: list[RunContext] = []

    async def execute(self, context: RunContext) -> RunResult:
        """Execute the agent run mock."""
        self.executed_contexts.append(context)
        tracer = get_tracer("varistha.runtime")

        with tracer.start_as_current_span(
            "llm.call",
            attributes={
                GEN_AI_SYSTEM: "mock",
                GEN_AI_REQUEST_MODEL: context.model,
                GEN_AI_USAGE_TOTAL_TOKENS: self.tokens,
                VARISTHA_COST_USD: self.cost_usd,
            },
        ) as span:
            if self.should_fail:
                span.set_status(trace.StatusCode.ERROR, self.error_message)
                return RunResult(
                    status="failed",
                    output={},
                    cost_usd=self.cost_usd,
                    total_tokens=self.tokens,
                    error=self.error_message,
                )

            if self.waiting_approval:
                span.set_status(trace.StatusCode.OK)
                return RunResult(
                    status="waiting_approval",
                    output=self.default_output or {"proposal": "Mock action pending human review"},
                    cost_usd=self.cost_usd,
                    total_tokens=self.tokens,
                    error=None,
                )

            span.set_status(trace.StatusCode.OK)
            output = self.default_output or {
                "result": f"Executed agent '{context.agent_name}' with model '{context.model}'",
                "received_input": context.input_data,
            }

            return RunResult(
                status="completed",
                output=output,
                cost_usd=self.cost_usd,
                total_tokens=self.tokens,
                error=None,
            )
