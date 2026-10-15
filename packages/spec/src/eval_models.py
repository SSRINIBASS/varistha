"""Pydantic v2 declarative models for Varistha Evaluation Suites.

Defines the canonical ``varistha/v1 EvalSuite`` document structure
supporting test datasets, multi-evaluator assertions, and pass-rate gates.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

EvaluatorType = Literal[
    "exact-match",
    "contains",
    "regex",
    "json-schema",
    "semantic-similarity",
    "llm-rubric",
    "custom",
]


class EvaluatorConfig(BaseModel):
    """Configuration for an evaluator assertion in an eval suite."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Unique name of the evaluator in this suite.")
    type: EvaluatorType = Field(..., description="Evaluation assertion type.")
    model: str | None = Field(
        default=None,
        description="LiteLLM model string for llm-rubric (e.g. gpt-4o, claude-3-5-sonnet).",
    )
    rubric: str | None = Field(
        default=None,
        description="Scoring criteria or prompt template for llm-rubric evaluators.",
    )
    schema_def: dict[str, Any] | None = Field(
        default=None,
        alias="schema",
        description="JSON Schema dictionary when type is json-schema.",
    )
    threshold: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score threshold (0.0 to 1.0) required to consider check passed.",
    )


class TestCaseConfig(BaseModel):
    """An individual test scenario / dataset row."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for the test case.")
    name: str = Field(..., description="Human-readable title describing the test scenario.")
    input: dict[str, Any] = Field(..., description="Input payload passed into the agent run.")
    expected: Any | None = Field(
        default=None,
        description="Expected ground truth, schema, or reference answer.",
    )
    evaluators: list[str] | None = Field(
        default=None,
        description="List of evaluator names from the suite to run on this case. Defaults to all.",
    )
    tags: list[str] = Field(
        default_factory=list, description="Categorization tags (e.g. edge-case, smoke)."
    )


class EvalSuiteMetadata(BaseModel):
    """Metadata block for an eval suite."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Slug identifier for the evaluation suite.")
    agent: str = Field(..., description="Target agent name / slug.")
    version: str | None = Field(default=None, description="Optional version of this eval suite.")
    owner: str | None = Field(default=None, description="Owner email or team identifier.")

    @field_validator("name", "agent")
    @classmethod
    def must_be_slug(cls, value: str) -> str:
        """Enforce lowercase slug format."""
        if not _SLUG_RE.match(value):
            msg = f"'{value}' must match [a-z0-9][a-z0-9-]*."
            raise ValueError(msg)
        return value


class EvalSuiteSpec(BaseModel):
    """Spec block for an eval suite."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(
        default=None, description="Detailed purpose of this eval suite."
    )
    evaluators: list[EvaluatorConfig] = Field(
        default_factory=list,
        description="Evaluators configured for this suite.",
    )
    cases: list[TestCaseConfig] = Field(
        default_factory=list,
        description="Test cases / evaluation dataset records.",
    )


class EvalSuiteDoc(BaseModel):
    """Canonical top-level document for a Varistha Eval Suite."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Literal["varistha/v1"] = Field(  # noqa: N815
        default="varistha/v1",
        description="API version; must be varistha/v1.",
    )
    kind: Literal["EvalSuite"] = Field(
        default="EvalSuite",
        description="Resource kind; must be EvalSuite.",
    )
    metadata: EvalSuiteMetadata = Field(..., description="Identity and agent binding metadata.")
    spec: EvalSuiteSpec = Field(..., description="Evaluator definitions and dataset test cases.")
