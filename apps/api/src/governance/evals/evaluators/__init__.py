"""Evaluator library and factory initialization."""

from __future__ import annotations

from typing import Any

from governance.evals.evaluators.builtin import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    GroundingEvaluator,
    JsonSchemaEvaluator,
    LLMRubricEvaluator,
    RegexEvaluator,
)
from governance.evals.evaluators.interface import BaseEvaluator, EvaluatorOutcome

EVALUATOR_REGISTRY: dict[str, Any] = {
    "exact-match": ExactMatchEvaluator,
    "contains": ContainsEvaluator,
    "regex": RegexEvaluator,
    "json-schema": JsonSchemaEvaluator,
    "semantic-similarity": GroundingEvaluator,
    "grounding": GroundingEvaluator,
    "llm-rubric": LLMRubricEvaluator,
}


def create_evaluator(config: dict[str, Any]) -> BaseEvaluator:
    """Instantiate an evaluator from configuration dictionary."""
    eval_type = config.get("type", "exact-match")
    name = config.get("name", eval_type)
    threshold = float(config.get("threshold", 1.0))

    eval_cls = EVALUATOR_REGISTRY.get(eval_type)
    if not eval_cls:
        msg = f"Unknown evaluator type: '{eval_type}'. Available: {list(EVALUATOR_REGISTRY.keys())}"
        raise ValueError(msg)

    return eval_cls(name=name, threshold=threshold, config=config)


__all__ = [
    "EVALUATOR_REGISTRY",
    "BaseEvaluator",
    "ContainsEvaluator",
    "EvaluatorOutcome",
    "ExactMatchEvaluator",
    "GroundingEvaluator",
    "JsonSchemaEvaluator",
    "LLMRubricEvaluator",
    "RegexEvaluator",
    "create_evaluator",
]
