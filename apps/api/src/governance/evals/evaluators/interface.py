"""Interface and base abstractions for evaluation assertions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluatorOutcome:
    """Outcome of evaluating an assertion on an agent output."""

    passed: bool
    score: float
    failure_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseEvaluator(ABC):
    """Abstract base class for all evaluation assertion engines."""

    def __init__(
        self,
        name: str,
        evaluator_type: str,
        threshold: float = 1.0,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the evaluator with name, type, score threshold, and optional config."""
        self.name = name
        self.evaluator_type = evaluator_type
        self.threshold = threshold
        self.config = config or {}

    @abstractmethod
    async def evaluate(
        self,
        actual: Any,
        expected: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> EvaluatorOutcome:
        """Evaluate agent output against expected reference or criteria."""
        raise NotImplementedError
