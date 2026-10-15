"""Unit tests for EvalSuite declarative schema models."""

import pytest
from pydantic import ValidationError

from spec import EvalSuiteDoc, EvaluatorConfig, TestCaseConfig


def test_valid_eval_suite_minimal():
    data = {
        "apiVersion": "varistha/v1",
        "kind": "EvalSuite",
        "metadata": {
            "name": "lead-qualification-suite",
            "agent": "lead-researcher",
            "version": "1.0.0",
        },
        "spec": {
            "description": "Tests lead qualification accuracy.",
            "evaluators": [
                {
                    "name": "company-contains",
                    "type": "contains",
                },
                {
                    "name": "schema-valid",
                    "type": "json-schema",
                    "schema": {
                        "type": "object",
                        "properties": {"company": {"type": "string"}},
                    },
                },
            ],
            "cases": [
                {
                    "id": "tc-1",
                    "name": "Acme Cloud Series A",
                    "input": {"company": "Acme Cloud"},
                    "expected": {"company": "Acme Cloud"},
                    "evaluators": ["company-contains"],
                    "tags": ["smoke"],
                }
            ],
        },
    }

    doc = EvalSuiteDoc.model_validate(data)
    assert doc.metadata.name == "lead-qualification-suite"
    assert doc.metadata.agent == "lead-researcher"
    assert len(doc.spec.evaluators) == 2
    assert len(doc.spec.cases) == 1
    assert doc.spec.cases[0].id == "tc-1"


def test_invalid_suite_name_rejected():
    with pytest.raises(ValidationError):
        EvalSuiteDoc.model_validate(
            {
                "apiVersion": "varistha/v1",
                "kind": "EvalSuite",
                "metadata": {
                    "name": "Invalid_Suite Name!",
                    "agent": "lead-researcher",
                },
                "spec": {},
            }
        )


def test_invalid_evaluator_type():
    with pytest.raises(ValidationError):
        EvaluatorConfig(name="test", type="unknown-evaluator")  # type: ignore[arg-type]


def test_test_case_defaults():
    tc = TestCaseConfig(
        id="tc-100",
        name="Simple test case",
        input={"prompt": "hello"},
    )
    assert tc.expected is None
    assert tc.evaluators is None
    assert tc.tags == []
