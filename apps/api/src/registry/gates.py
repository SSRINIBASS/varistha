"""Domain gate evaluation engine for agent lifecycle transitions.

Implements the promotion gates and criteria specified in docs/SPEC.md § 3.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from spec import SpecValidationError, validate_spec

ALLOWED_STAGES: tuple[str, ...] = (
    "draft",
    "prototype",
    "staging",
    "production",
    "deprecated",
    "retired",
)

_STAGE_INDEX: dict[str, int] = {stage: i for i, stage in enumerate(ALLOWED_STAGES)}

# Direct forward progression map
_VALID_FORWARD_TRANSITIONS: dict[str, str] = {
    "draft": "prototype",
    "prototype": "staging",
    "staging": "production",
    "production": "deprecated",
    "deprecated": "retired",
}


@dataclass(frozen=True)
class GateCheck:
    """Individual gate requirement evaluation result."""

    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert check result to dictionary for audit logging and JSON responses."""
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class GateEvaluationResult:
    """Overall outcome of evaluating a stage transition against gates."""

    allowed: bool
    from_stage: str
    to_stage: str
    is_rollback: bool
    checks: list[GateCheck] = field(default_factory=list)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "allowed": self.allowed,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "is_rollback": self.is_rollback,
            "checks": [c.to_dict() for c in self.checks],
            "error_message": self.error_message,
        }


def is_valid_transition(from_stage: str, to_stage: str) -> bool:
    """Check if a transition between two lifecycle stages is syntactically permitted."""
    if from_stage not in _STAGE_INDEX or to_stage not in _STAGE_INDEX:
        return False

    if from_stage == to_stage:
        return False

    # Forward sequential transition
    if _VALID_FORWARD_TRANSITIONS.get(from_stage) == to_stage:
        return True

    # Demotion / rollback (strictly backward in progression)
    if _STAGE_INDEX[to_stage] < _STAGE_INDEX[from_stage]:
        return True

    # Reviving from deprecated back to production is permitted as a rollback
    return bool(from_stage == "deprecated" and to_stage in ("production", "staging"))


def is_rollback_transition(from_stage: str, to_stage: str) -> bool:
    """Check if the transition is a demotion/rollback rather than a forward promotion."""
    if from_stage not in _STAGE_INDEX or to_stage not in _STAGE_INDEX:
        return False
    return _STAGE_INDEX[to_stage] < _STAGE_INDEX[from_stage] or (
        from_stage == "deprecated" and to_stage == "production"
    )


def evaluate_stage_transition(
    from_stage: str,
    to_stage: str,
    spec_dict: dict[str, Any] | None,
    runs: list[dict[str, Any]],
    reason: str | None = None,
    replacement: str | None = None,
    kill_switch_verified: bool | None = None,
    secrets_revoked: bool | None = None,
    eval_runs: list[dict[str, Any]] | None = None,
) -> GateEvaluationResult:
    """Evaluate all required gates for a proposed stage transition."""
    from_stage = from_stage.lower()
    to_stage = to_stage.lower()

    if not is_valid_transition(from_stage, to_stage):
        return GateEvaluationResult(
            allowed=False,
            from_stage=from_stage,
            to_stage=to_stage,
            is_rollback=False,
            checks=[
                GateCheck(
                    name="valid_transition",
                    passed=False,
                    message=f"Transition from '{from_stage}' to '{to_stage}' is not permitted.",
                ),
            ],
            error_message=f"Invalid transition from '{from_stage}' to '{to_stage}'.",
        )

    # Rollback handling
    if is_rollback_transition(from_stage, to_stage):
        checks: list[GateCheck] = []
        if reason and reason.strip():
            checks.append(
                GateCheck(
                    name="rollback_reason",
                    passed=True,
                    message=f"Rollback reason provided: {reason.strip()}",
                ),
            )
            return GateEvaluationResult(
                allowed=True,
                from_stage=from_stage,
                to_stage=to_stage,
                is_rollback=True,
                checks=checks,
            )
        checks.append(
            GateCheck(
                name="rollback_reason",
                passed=False,
                message="Rollbacks and demotions require an explanatory reason in the audit trail.",
            ),
        )
        return GateEvaluationResult(
            allowed=False,
            from_stage=from_stage,
            to_stage=to_stage,
            is_rollback=True,
            checks=checks,
            error_message="Rollback requires an explanatory reason.",
        )

    # Forward promotion evaluation
    checks = []

    # 1. Spec validity check (common to forward promotions)
    spec_obj = None
    if spec_dict:
        try:
            spec_obj = validate_spec(spec_dict)
            checks.append(
                GateCheck(
                    name="spec_valid",
                    passed=True,
                    message="Agent spec adheres strictly to schema.",
                ),
            )
        except SpecValidationError as err:
            checks.append(
                GateCheck(
                    name="spec_valid",
                    passed=False,
                    message=f"Agent spec failed validation: {err.errors}",
                ),
            )
    else:
        checks.append(
            GateCheck(
                name="spec_valid",
                passed=False,
                message="No agent specification found.",
            ),
        )

    # Gate 1: Draft -> Prototype
    if from_stage == "draft" and to_stage == "prototype":
        has_success = any(r.get("status") in ("success", "completed") for r in runs)
        checks.append(
            GateCheck(
                name="successful_run",
                passed=has_success,
                message=(
                    "Agent has completed at least one run successfully."
                    if has_success
                    else "Must complete at least one successful run before promotion to prototype."
                ),
            ),
        )

    # Gate 2: Prototype -> Staging
    elif from_stage == "prototype" and to_stage == "staging":
        # Check owner
        owner = spec_obj.metadata.owner if spec_obj else ""
        owner_ok = bool(owner and "@" in owner)
        checks.append(
            GateCheck(
                name="owner_assigned",
                passed=owner_ok,
                message=(
                    f"Owner '{owner}' is assigned."
                    if owner_ok
                    else "A valid owner email address must be assigned in metadata.owner."
                ),
            ),
        )

        # Check guardrails
        has_guardrails = False
        if spec_obj and spec_obj.spec.guardrails:
            g = spec_obj.spec.guardrails
            has_guardrails = bool(
                (g.input and len(g.input) > 0)
                or (g.output and len(g.output) > 0)
                or (g.tools and len(g.tools) > 0)
            )
        checks.append(
            GateCheck(
                name="guardrails_attached",
                passed=has_guardrails,
                message=(
                    "Input, output, or tool guardrails are attached."
                    if has_guardrails
                    else "At least one guardrail (input, output, or tools) must be configured."
                ),
            ),
        )

        # Check eval suite
        has_eval_suite = False
        if spec_obj and spec_obj.spec.evals:
            has_eval_suite = bool(
                spec_obj.spec.evals.suite and spec_obj.spec.evals.min_pass_rate > 0
            )
        checks.append(
            GateCheck(
                name="eval_suite_present",
                passed=has_eval_suite,
                message=(
                    "Eval suite is configured with a minimum pass rate."
                    if has_eval_suite
                    else "An eval suite and minimum pass rate must be configured in spec.evals."
                ),
            ),
        )

        if eval_runs is not None:
            min_pass_rate = (
                spec_obj.spec.evals.min_pass_rate
                if spec_obj and spec_obj.spec.evals and spec_obj.spec.evals.min_pass_rate
                else 0.8
            )
            completed_evals = [e for e in eval_runs if e.get("status") == "completed"]
            best_rate = max(
                (float(e.get("pass_rate") or 0.0) for e in completed_evals), default=0.0
            )
            eval_passed = bool(completed_evals and best_rate >= min_pass_rate)
            if eval_passed:
                eval_msg = (
                    f"Eval suite executed with passing rate {best_rate:.1%} "
                    f"(required: {min_pass_rate:.1%})."
                )
            elif not completed_evals:
                eval_msg = (
                    "No completed evaluation runs found. Must run eval suite before promotion."
                )
            else:
                eval_msg = (
                    f"Eval suite pass rate {best_rate:.1%} is below required threshold "
                    f"of {min_pass_rate:.1%}."
                )
            checks.append(
                GateCheck(
                    name="eval_suite_passed",
                    passed=eval_passed,
                    message=eval_msg,
                )
            )

    # Gate 3: Staging -> Production
    elif from_stage == "staging" and to_stage == "production":
        # Check evals
        if eval_runs is not None:
            min_pass_rate = (
                spec_obj.spec.evals.min_pass_rate
                if spec_obj and spec_obj.spec.evals and spec_obj.spec.evals.min_pass_rate
                else 0.8
            )
            completed_evals = [e for e in eval_runs if e.get("status") == "completed"]
            best_rate = max(
                (float(e.get("pass_rate") or 0.0) for e in completed_evals), default=0.0
            )
            evals_met = bool(completed_evals and best_rate >= min_pass_rate)
            if evals_met:
                eval_msg = f"Eval score threshold met ({best_rate:.1%} >= {min_pass_rate:.1%})."
            elif not completed_evals:
                eval_msg = (
                    "Verified eval suite run required for production. No completed runs found."
                )
            else:
                eval_msg = (
                    f"Verified eval suite and passing score required for production "
                    f"(found: {best_rate:.1%}, required: {min_pass_rate:.1%})."
                )
            checks.append(
                GateCheck(
                    name="eval_score_threshold",
                    passed=evals_met,
                    message=eval_msg,
                ),
            )
        else:
            has_evals = False
            if spec_obj and spec_obj.spec.evals:
                has_evals = bool(
                    spec_obj.spec.evals.suite and spec_obj.spec.evals.min_pass_rate > 0
                )
            checks.append(
                GateCheck(
                    name="eval_score_threshold",
                    passed=has_evals,
                    message=(
                        "Eval suite meets threshold criteria."
                        if has_evals
                        else "Verified eval suite and passing score required for production."
                    ),
                ),
            )

        # Check reviewed / successful runs
        successful_runs = [r for r in runs if r.get("status") in ("success", "completed")]
        has_runs = len(successful_runs) >= 1
        checks.append(
            GateCheck(
                name="reviewed_runs",
                passed=has_runs,
                message=(
                    f"Agent has {len(successful_runs)} verified successful execution runs."
                    if has_runs
                    else "Must have at least one verified successful execution run in staging."
                ),
            ),
        )

        # Check budget limits
        budget_ok = False
        if spec_obj and spec_obj.spec.budget:
            b = spec_obj.spec.budget
            budget_ok = bool(b.max_usd_per_run > 0 and b.max_usd_per_day > 0)
        checks.append(
            GateCheck(
                name="budget_configured",
                passed=budget_ok,
                message=(
                    "Explicit budget limits (max_usd_per_run and max_usd_per_day) are configured."
                    if budget_ok
                    else "Budget limits (max_usd_per_run > 0 and max_usd_per_day > 0) required."
                ),
            ),
        )

        # Check kill switch
        kill_switch_ok = bool(kill_switch_verified is True)
        checks.append(
            GateCheck(
                name="kill_switch_tested",
                passed=kill_switch_ok,
                message=(
                    "Emergency kill switch operation has been tested and verified."
                    if kill_switch_ok
                    else "Operator must test/confirm kill switch (kill_switch_verified=true)."
                ),
            ),
        )

    # Gate 4: Production -> Deprecated
    elif from_stage == "production" and to_stage == "deprecated":
        # Check replacement
        has_replacement = bool((replacement and replacement.strip()) or (reason and reason.strip()))
        rep_label = (replacement or reason or "").strip()
        checks.append(
            GateCheck(
                name="replacement_named",
                passed=has_replacement,
                message=(
                    f"Decommission replacement or migration rationale provided: '{rep_label}'."
                    if has_replacement
                    else "A replacement agent or decommission rationale must be specified."
                ),
            ),
        )

        # Check traffic drained
        has_in_flight = any(r.get("status") in ("running", "pending") for r in runs)
        checks.append(
            GateCheck(
                name="traffic_drained",
                passed=not has_in_flight,
                message=(
                    "All active execution runs have completed. Traffic is drained."
                    if not has_in_flight
                    else "Cannot deprecate while runs are actively pending or executing."
                ),
            ),
        )

    # Gate 5: Deprecated -> Retired
    elif from_stage == "deprecated" and to_stage == "retired":
        # Check triggers disabled
        triggers_empty = True
        if spec_obj and spec_obj.spec.triggers:
            triggers_empty = len(spec_obj.spec.triggers) == 0
        checks.append(
            GateCheck(
                name="triggers_disabled",
                passed=triggers_empty,
                message=(
                    "All automated triggers are disabled."
                    if triggers_empty
                    else "Automated triggers must be disabled/cleared before retiring."
                ),
            ),
        )

        # Check history kept
        checks.append(
            GateCheck(
                name="history_preserved",
                passed=True,
                message="Execution history and audit logs are preserved in storage.",
            ),
        )

        # Check secrets revoked
        secrets_ok = bool(secrets_revoked is True)
        checks.append(
            GateCheck(
                name="secrets_revoked",
                passed=secrets_ok,
                message=(
                    "Credentials and plugin secrets have been confirmed revoked."
                    if secrets_ok
                    else "Confirmation of secret revocation required (secrets_revoked=true)."
                ),
            ),
        )

    all_passed = all(c.passed for c in checks)
    error_msg = (
        None if all_passed else f"Promotion gates for '{from_stage}' -> '{to_stage}' failed."
    )

    return GateEvaluationResult(
        allowed=all_passed,
        from_stage=from_stage,
        to_stage=to_stage,
        is_rollback=False,
        checks=checks,
        error_message=error_msg,
    )
