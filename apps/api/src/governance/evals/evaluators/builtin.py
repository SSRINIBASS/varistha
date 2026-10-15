"""Builtin evaluator implementations for offline evaluation suites."""

from __future__ import annotations

import json
import re
from typing import Any

import jsonschema
from governance.evals.evaluators.interface import BaseEvaluator, EvaluatorOutcome


class ExactMatchEvaluator(BaseEvaluator):
    """Evaluates strict deep equality between actual output and expected ground truth."""

    def __init__(
        self,
        name: str = "exact-match",
        threshold: float = 1.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize exact match evaluator."""
        super().__init__(
            name=name,
            evaluator_type="exact-match",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate if actual output exactly matches expected reference."""
        if isinstance(actual, str) and isinstance(expected, str):
            match = actual.strip() == expected.strip()
        else:
            match = actual == expected

        score = 1.0 if match else 0.0
        passed = score >= self.threshold
        failure_reason = None if passed else f"Expected '{expected}' but received '{actual}'"

        return EvaluatorOutcome(
            passed=passed,
            score=score,
            failure_reason=failure_reason,
            metadata={"expected": expected, "actual": actual},
        )


class ContainsEvaluator(BaseEvaluator):
    """Evaluates whether expected substring or key/values exist within output."""

    def __init__(
        self,
        name: str = "contains",
        threshold: float = 1.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize contains evaluator."""
        super().__init__(
            name=name,
            evaluator_type="contains",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate whether actual output contains expected substring, key, or item."""
        match = False
        target = self.config.get("value", expected)

        if isinstance(actual, str) and target is not None:
            match = str(target).lower() in actual.lower()
        elif isinstance(actual, dict) and isinstance(target, dict):
            match = all(actual.get(k) == v for k, v in target.items())
        elif isinstance(actual, (list, set, tuple)) and target is not None:
            match = target in actual
        elif actual is not None and target is not None:
            match = str(target) in str(actual)

        score = 1.0 if match else 0.0
        passed = score >= self.threshold
        failure_reason = None if passed else f"Output did not contain expected content: '{target}'"

        return EvaluatorOutcome(
            passed=passed,
            score=score,
            failure_reason=failure_reason,
            metadata={"target": target},
        )


class RegexEvaluator(BaseEvaluator):
    """Evaluates whether actual output matches a regular expression pattern."""

    def __init__(
        self,
        name: str = "regex",
        threshold: float = 1.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize regex pattern evaluator."""
        super().__init__(
            name=name,
            evaluator_type="regex",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate whether actual output matches configured regex pattern."""
        pattern = str(self.config.get("pattern") or expected or "")
        try:
            match = bool(re.search(pattern, str(actual), re.DOTALL | re.IGNORECASE))
        except re.error as err:
            return EvaluatorOutcome(
                passed=False,
                score=0.0,
                failure_reason=f"Invalid regex pattern '{pattern}': {err}",
            )

        score = 1.0 if match else 0.0
        passed = score >= self.threshold
        failure_reason = None if passed else f"Output did not match regex pattern: '{pattern}'"

        return EvaluatorOutcome(
            passed=passed,
            score=score,
            failure_reason=failure_reason,
            metadata={"pattern": pattern},
        )


class JsonSchemaEvaluator(BaseEvaluator):
    """Evaluates JSON Schema conformity of structured agent output."""

    def __init__(
        self,
        name: str = "json-schema",
        threshold: float = 1.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize JSON Schema evaluator."""
        super().__init__(
            name=name,
            evaluator_type="json-schema",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Validate actual output dictionary or JSON string against JSON Schema."""
        schema = self.config.get("schema") or expected
        if not schema or not isinstance(schema, dict):
            return EvaluatorOutcome(
                passed=False,
                score=0.0,
                failure_reason="No valid JSON Schema definition provided for evaluator.",
            )

        instance = actual
        if isinstance(actual, str):
            try:
                instance = json.loads(actual)
            except json.JSONDecodeError as err:
                return EvaluatorOutcome(
                    passed=False,
                    score=0.0,
                    failure_reason=f"Output is not valid JSON string: {err}",
                )

        try:
            jsonschema.validate(instance=instance, schema=schema)
            return EvaluatorOutcome(passed=True, score=1.0)
        except jsonschema.ValidationError as err:
            return EvaluatorOutcome(
                passed=False,
                score=0.0,
                failure_reason=(
                    f"JSON Schema validation error: {err.message} at path {list(err.path)}"
                ),
                metadata={"error_path": list(err.path)},
            )


class GroundingEvaluator(BaseEvaluator):
    """Evaluates grounding and citation coverage against input context."""

    def __init__(
        self,
        name: str = "grounding",
        threshold: float = 0.5,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize grounding overlap evaluator."""
        super().__init__(
            name=name,
            evaluator_type="grounding",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate grounding ratio by measuring keyword overlap with input context."""
        input_data = (context or {}).get("input") or expected or ""
        source_text = json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)
        out_text = json.dumps(actual) if isinstance(actual, dict) else str(actual)

        source_words = set(re.findall(r"\b\w{3,}\b", source_text.lower()))
        out_words = set(re.findall(r"\b\w{3,}\b", out_text.lower()))

        if not out_words:
            return EvaluatorOutcome(passed=True, score=1.0)

        overlap = out_words.intersection(source_words)
        ratio = len(overlap) / len(out_words)
        score = round(ratio, 4)
        passed = score >= self.threshold
        failure_reason = (
            None
            if passed
            else f"Grounding ratio {score:.2f} is below threshold {self.threshold:.2f}."
        )

        return EvaluatorOutcome(
            passed=passed,
            score=score,
            failure_reason=failure_reason,
            metadata={"overlap_terms": len(overlap), "total_terms": len(out_words)},
        )


class LLMRubricEvaluator(BaseEvaluator):
    """Evaluates agent output using an LLM-as-a-judge rubric via LiteLLM."""

    def __init__(
        self,
        name: str = "llm-rubric",
        threshold: float = 0.8,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LLM-as-a-judge evaluator."""
        super().__init__(
            name=name,
            evaluator_type="llm-rubric",
            threshold=threshold,
            config=config,
        )

    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate agent output using an LLM judge and prompt rubric."""
        import litellm

        model = self.config.get("model") or "gpt-4o-mini"
        rubric = self.config.get("rubric") or (
            "Evaluate if candidate output fulfills user request and matches ground truth. "
            "Return JSON with 'score' (float 0.0 to 1.0) and 'reasoning' (string)."
        )

        prompt = (
            f"You are an expert impartial evaluation judge.\n\n"
            f"RUBRIC:\n{rubric}\n\n"
            f"INPUT:\n{json.dumps((context or {}).get('input'), default=str)}\n\n"
            f"EXPECTED OUTPUT:\n{json.dumps(expected, default=str)}\n\n"
            f"ACTUAL OUTPUT TO GRADE:\n{json.dumps(actual, default=str)}\n\n"
            f"Respond ONLY with valid JSON in this exact structure:\n"
            f'{{"score": 0.95, "reasoning": "Detailed justification here."}}\n'
        )

        try:
            resp: Any = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            parsed = json.loads(content)
            score = float(parsed.get("score", 0.0))
            reasoning = str(parsed.get("reasoning", ""))
            passed = score >= self.threshold
            fail_msg = (
                None
                if passed
                else f"LLM judge scored {score:.2f} (< {self.threshold:.2f}): {reasoning}"
            )

            return EvaluatorOutcome(
                passed=passed,
                score=score,
                failure_reason=fail_msg,
                metadata={"judge_model": model, "reasoning": reasoning},
            )
        except Exception as err:
            return EvaluatorOutcome(
                passed=False,
                score=0.0,
                failure_reason=f"LLM rubric evaluator error: {err}",
                metadata={"error": str(err)},
            )
