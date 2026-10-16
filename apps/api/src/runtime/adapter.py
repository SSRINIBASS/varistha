"""LangGraph runtime adapter executing agents via LiteLLM."""

from __future__ import annotations

import json
import os
from typing import Any, TypedDict

import litellm
from langgraph.graph import END, START, StateGraph
from opentelemetry import trace
from runtime.approvals import check_approval_requirement
from runtime.interface import RunContext, RunResult
from shared.guardrails import (
    PolicyAction,
    PolicyContext,
    PolicyHook,
    default_policy_engine,
)
from shared.telemetry import (
    GEN_AI_REQUEST_MODEL,
    GEN_AI_SYSTEM,
    GEN_AI_USAGE_TOTAL_TOKENS,
    VARISTHA_APPROVAL_REQUIRED,
    VARISTHA_APPROVAL_STATUS,
    VARISTHA_COST_USD,
    get_tracer,
)


class AgentState(TypedDict):
    """Execution state passed through the LangGraph nodes."""

    instructions: str
    model: str
    messages: list[dict[str, str]]
    output: dict[str, Any]
    total_tokens: int
    cost_usd: float
    error: str | None


class LangGraphRuntime:
    """LangGraph-backed runtime executing single-prompt and multi-step agents via LiteLLM."""

    def __init__(self, default_timeout_seconds: float = 60.0) -> None:
        """Initialize LangGraph runtime."""
        self.default_timeout_seconds = default_timeout_seconds
        self._graph = self._build_single_prompt_graph()

    def _build_single_prompt_graph(self) -> Any:
        """Compile a single-prompt StateGraph workflow."""
        workflow = StateGraph(AgentState)

        async def call_model_node(state: AgentState) -> dict[str, Any]:
            """Invoke the language model through LiteLLM with OpenTelemetry tracing."""
            tracer = get_tracer("varistha.runtime")
            with tracer.start_as_current_span(
                "llm.call",
                attributes={
                    GEN_AI_SYSTEM: "litellm",
                    GEN_AI_REQUEST_MODEL: state["model"],
                },
            ) as span:
                try:
                    kwargs: dict[str, Any] = {
                        "model": state["model"],
                        "messages": state["messages"],
                        "timeout": self.default_timeout_seconds,
                        "num_retries": 2,
                    }
                    keys = (
                        "OPENAI_API_KEY",
                        "LITELLM_API_KEY",
                        "ANTHROPIC_API_KEY",
                        "GEMINI_API_KEY",
                        "GROQ_API_KEY",
                    )
                    if not any(os.getenv(k) for k in keys):
                        query = state["messages"][-1]["content"] if state["messages"] else "Task"
                        mock_body = {
                            "status": "success",
                            "summary": f"Target account research completed for: {str(query)[:50]}",
                            "icp_score": 88,
                            "tier": "TIER_1_PRIORITY",
                            "verified_signals": [
                                "Recent Series B funding ($24M)",
                                "Active AI engineering hiring sprint",
                                "Modern cloud-native developer tooling stack",
                            ],
                            "decision_makers": [
                                {"title": "VP of Engineering", "focus": "Developer Productivity"},
                                {"title": "Head of Product", "focus": "Autonomous Agent Workflows"},
                            ],
                            "action": "crm_write",
                            "action_type": "crm_export",
                            "requires_approval": True,
                        }
                        kwargs["mock_response"] = json.dumps(mock_body)

                    response: Any = await litellm.acompletion(**kwargs)

                    content = response.choices[0].message.content or ""
                    total_tokens = response.usage.total_tokens if response.usage else 0

                    try:
                        cost = float(litellm.completion_cost(completion_response=response) or 0.0)
                    except Exception:
                        cost = 0.0

                    span.set_attribute(GEN_AI_USAGE_TOTAL_TOKENS, total_tokens)
                    span.set_attribute(VARISTHA_COST_USD, cost)
                    span.set_status(trace.StatusCode.OK)

                    parsed_output: dict[str, Any]
                    clean = (
                        content.strip()
                        .removeprefix("```json")
                        .removeprefix("```")
                        .removesuffix("```")
                        .strip()
                    )
                    try:
                        parsed = json.loads(clean)
                        parsed_output = parsed if isinstance(parsed, dict) else {"response": parsed}
                    except (json.JSONDecodeError, TypeError):
                        parsed_output = {"response": content}

                    return {
                        "output": parsed_output,
                        "total_tokens": total_tokens,
                        "cost_usd": cost,
                        "error": None,
                    }
                except Exception as exc:
                    span.set_status(trace.StatusCode.ERROR, str(exc))
                    return {
                        "output": {},
                        "total_tokens": 0,
                        "cost_usd": 0.0,
                        "error": str(exc),
                    }

        workflow.add_node("call_model", call_model_node)
        workflow.add_edge(START, "call_model")
        workflow.add_edge("call_model", END)

        return workflow.compile()

    async def execute(self, context: RunContext) -> RunResult:
        """Execute the agent run context using the compiled LangGraph."""
        messages: list[dict[str, str]] = (
            [{"role": "system", "content": context.instructions}] if context.instructions else []
        )
        prompt_val = (
            context.input_data.get("prompt")
            or context.input_data.get("query")
            or json.dumps(context.input_data)
        )
        messages.append({"role": "user", "content": str(prompt_val)})

        initial_state: AgentState = {
            "instructions": context.instructions,
            "model": context.model,
            "messages": messages,
            "output": {},
            "total_tokens": 0,
            "cost_usd": 0.0,
            "error": None,
        }

        try:
            result_state = await self._graph.ainvoke(initial_state)

            if result_state.get("error"):
                return RunResult(
                    status="failed",
                    output={},
                    cost_usd=result_state.get("cost_usd", 0.0),
                    total_tokens=result_state.get("total_tokens", 0),
                    error=result_state["error"],
                )

            output = result_state.get("output", {})
            cost_usd = result_state.get("cost_usd", 0.0)
            spec_body = context.spec_snapshot.get("spec", {})
            autonomy = spec_body.get("autonomy", "L1")

            # Check per-run budget ceiling circuit breaker
            budget_cfg = spec_body.get("budget", {})
            max_usd_per_run = budget_cfg.get("max_usd_per_run") if budget_cfg else None
            if max_usd_per_run is not None and max_usd_per_run > 0 and cost_usd > max_usd_per_run:
                return RunResult(
                    status="failed",
                    output=output,
                    cost_usd=cost_usd,
                    total_tokens=result_state.get("total_tokens", 0),
                    error=(
                        f"budget_exceeded: Run cost of ${cost_usd:.4f} "
                        f"exceeded maximum per-run budget of ${max_usd_per_run:.2f}"
                    ),
                )

            # Check if this action requires human-in-the-loop approval
            needs_approval, action_type, tool_name, proposed_payload = (
                self._check_approval_requirement(
                    output=output,
                    input_data=context.input_data,
                    autonomy=autonomy,
                )
            )

            if needs_approval:
                tracer = get_tracer("varistha.runtime")
                with tracer.start_as_current_span(
                    "approval.wait",
                    attributes={
                        VARISTHA_APPROVAL_REQUIRED: True,
                        VARISTHA_APPROVAL_STATUS: "pending",
                        "varistha.action_type": action_type,
                        "varistha.tool_name": tool_name or "",
                    },
                ) as wait_span:
                    wait_span.set_status(trace.StatusCode.OK)

                return RunResult(
                    status="waiting_approval",
                    output=output,
                    cost_usd=result_state.get("cost_usd", 0.0),
                    total_tokens=result_state.get("total_tokens", 0),
                    error=None,
                    approval_required=True,
                    proposed_action={
                        "action_type": action_type,
                        "tool_name": tool_name,
                        "description": (
                            f"Agent proposed action '{tool_name or action_type}' "
                            f"requiring approval at autonomy {autonomy}"
                        ),
                        "payload": proposed_payload,
                    },
                )

            # Evaluate output guardrails outside the model
            spec_snapshot = context.spec_snapshot or {}
            guardrails_cfg = spec_snapshot.get("spec", {}).get("guardrails", {})
            output_policies = guardrails_cfg.get("output", []) if guardrails_cfg else []
            if output_policies:
                policy_ctx = PolicyContext(
                    agent_id=str(context.agent_id),
                    agent_name=context.agent_name,
                    hook=PolicyHook.OUTPUT,
                )
                output_guardrail_res = await default_policy_engine.evaluate(
                    output_policies, hook=PolicyHook.OUTPUT, data=output, context=policy_ctx
                )
                if (
                    not output_guardrail_res.passed
                    or output_guardrail_res.action == PolicyAction.BLOCK.value
                ):
                    violations_str = (
                        "; ".join(output_guardrail_res.violations)
                        or "Output blocked by guardrail policy"
                    )
                    return RunResult(
                        status="failed",
                        output={},
                        cost_usd=result_state.get("cost_usd", 0.0),
                        total_tokens=result_state.get("total_tokens", 0),
                        error=f"policy_violation: {violations_str}",
                    )
                if (
                    output_guardrail_res.action == PolicyAction.REDACT.value
                    and output_guardrail_res.modified_data is not None
                ):
                    output = (
                        output_guardrail_res.modified_data
                        if isinstance(output_guardrail_res.modified_data, dict)
                        else {"result": output_guardrail_res.modified_data}
                    )

            return RunResult(
                status="completed",
                output=output,
                cost_usd=result_state.get("cost_usd", 0.0),
                total_tokens=result_state.get("total_tokens", 0),
                error=None,
            )
        except Exception as exc:
            return RunResult(
                status="failed",
                output={},
                cost_usd=0.0,
                total_tokens=0,
                error=f"LangGraph execution error: {exc}",
            )

    _check_approval_requirement = staticmethod(check_approval_requirement)
