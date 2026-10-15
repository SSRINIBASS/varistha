"""Version regression comparator for offline evaluation runs."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from shared.db.models.eval import EvalRun


class TestCaseComparison(BaseModel):
    """Comparison of a single test case assertion between base and candidate runs."""

    case_id: str = Field(..., description="Test case identifier.")
    case_name: str = Field(..., description="Human-readable title describing scenario.")
    base_passed: bool | None = Field(default=None, description="Assertion outcome in base version.")
    base_score: float | None = Field(default=None, description="Score in base version.")
    candidate_passed: bool | None = Field(
        default=None, description="Assertion outcome in candidate version."
    )
    candidate_score: float | None = Field(default=None, description="Score in candidate version.")
    status: Literal["regressed", "improved", "unchanged", "added", "removed"] = Field(
        ...,
        description="Regression status: regressed, improved, unchanged, added, or removed.",
    )


class EvalComparisonReport(BaseModel):
    """Version-over-version evaluation regression comparison report."""

    suite_id: uuid.UUID = Field(..., description="Evaluation suite UUID.")
    base_run_id: uuid.UUID = Field(..., description="Base eval run UUID.")
    candidate_run_id: uuid.UUID = Field(..., description="Candidate eval run UUID.")
    base_version_id: uuid.UUID | None = Field(default=None, description="Base agent version UUID.")
    candidate_version_id: uuid.UUID | None = Field(
        default=None, description="Candidate agent version UUID."
    )
    base_pass_rate: float = Field(..., description="Pass rate of base run.")
    candidate_pass_rate: float = Field(..., description="Pass rate of candidate run.")
    pass_rate_delta: float = Field(
        ...,
        description="Candidate pass rate minus base pass rate (positive indicates improvement).",
    )
    status: Literal["improved", "regressed", "unchanged"] = Field(
        ..., description="Overall version regression verdict."
    )
    total_cases_compared: int = Field(..., description="Number of unique test cases compared.")
    regressions_count: int = Field(
        ..., description="Number of assertions that regressed from passed to failed."
    )
    improvements_count: int = Field(
        ..., description="Number of assertions that improved from failed to passed."
    )
    latency_delta_ms: int = Field(
        ..., description="Change in total execution duration (milliseconds)."
    )
    cases: list[TestCaseComparison] = Field(
        default_factory=list, description="Per-case comparative breakdown."
    )


def compare_eval_runs(base_run: EvalRun, candidate_run: EvalRun) -> EvalComparisonReport:
    """Compare two evaluation runs and identify regressions or improvements."""
    base_results = {r.case_id: r for r in (base_run.results or [])}
    candidate_results = {r.case_id: r for r in (candidate_run.results or [])}

    all_case_ids = list(dict.fromkeys(list(base_results.keys()) + list(candidate_results.keys())))

    compared_cases: list[TestCaseComparison] = []
    regressions = 0
    improvements = 0

    for cid in all_case_ids:
        b = base_results.get(cid)
        c = candidate_results.get(cid)

        case_name = c.case_name if c else (b.case_name if b else cid)

        b_passed = b.passed if b else None
        b_score = b.score if b else None
        c_passed = c.passed if c else None
        c_score = c.score if c else None

        if b is not None and c is not None:
            if b_passed is True and c_passed is False:
                status = "regressed"
                regressions += 1
            elif b_passed is False and c_passed is True:
                status = "improved"
                improvements += 1
            else:
                status = "unchanged"
        elif b is None and c is not None:
            status = "added"
        else:
            status = "removed"

        compared_cases.append(
            TestCaseComparison(
                case_id=cid,
                case_name=case_name,
                base_passed=b_passed,
                base_score=b_score,
                candidate_passed=c_passed,
                candidate_score=c_score,
                status=status,
            )
        )

    base_pr = float(base_run.pass_rate or 0.0)
    cand_pr = float(candidate_run.pass_rate or 0.0)
    delta = round(cand_pr - base_pr, 4)

    if regressions > 0 or delta < -0.01:
        verdict: Literal["improved", "regressed", "unchanged"] = "regressed"
    elif improvements > 0 or delta > 0.01:
        verdict = "improved"
    else:
        verdict = "unchanged"

    base_duration = base_run.duration_ms or 0
    cand_duration = candidate_run.duration_ms or 0
    latency_delta = cand_duration - base_duration

    return EvalComparisonReport(
        suite_id=base_run.suite_id,
        base_run_id=base_run.id,
        candidate_run_id=candidate_run.id,
        base_version_id=base_run.agent_version_id,
        candidate_version_id=candidate_run.agent_version_id,
        base_pass_rate=base_pr,
        candidate_pass_rate=cand_pr,
        pass_rate_delta=delta,
        status=verdict,
        total_cases_compared=len(all_case_ids),
        regressions_count=regressions,
        improvements_count=improvements,
        latency_delta_ms=latency_delta,
        cases=compared_cases,
    )
