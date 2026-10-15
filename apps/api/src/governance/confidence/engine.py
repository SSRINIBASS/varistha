"""Verifiable confidence signal calculation and review-priority evaluation engine."""

from __future__ import annotations

import json
import re
import uuid
from typing import TYPE_CHECKING, Any

import jsonschema
from governance.confidence.schemas import (
    ConfidenceEvaluationRequest,
    ConfidenceSignal,
    ReviewPriorityOutcome,
)
from shared.db.models.approval import Approval
from shared.db.models.eval import EvalRun
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ReviewPriorityEngine:
    """Calculates review-priority and confidence from verifiable multi-source signals."""

    async def evaluate(
        self,
        db: AsyncSession,
        request: ConfidenceEvaluationRequest,
    ) -> ReviewPriorityOutcome:
        """Evaluate verifiable signals and compute review-priority score."""
        signals: list[ConfidenceSignal] = []

        # 1. Verifiable Schema Validation Signal (Weight 0.25)
        schema_signal = self._evaluate_schema(request.output, request.schema_def)
        signals.append(schema_signal)

        # 2. Grounding & Citation Overlap Signal (Weight 0.25)
        grounding_signal = self._evaluate_grounding(request.output, request.input_context)
        signals.append(grounding_signal)

        # 3. Offline Eval Benchmark Pass Rate Signal (Weight 0.25)
        eval_signal = await self._evaluate_eval_benchmark(db, request.agent_id, request.version_id)
        signals.append(eval_signal)

        # 4. Historical Approval Rate Signal (Weight 0.25)
        approval_signal = await self._evaluate_approval_history(db, request.agent_id)
        signals.append(approval_signal)

        # Synthesize weighted confidence score
        total_weight = sum(s.weight for s in signals)
        weighted_sum = sum(s.weight * s.score for s in signals)
        confidence_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

        # Classify Review Priority
        if confidence_score >= 0.8:
            priority = "low"
            rationale = (
                "High verifiable confidence across schema, grounding, and evaluation benchmarks."
            )
        elif confidence_score >= 0.6:
            priority = "medium"
            rationale = "Moderate confidence; routine review recommended."
        elif confidence_score >= 0.4:
            priority = "high"
            rationale = (
                "Low confidence detected in grounding, evals, or historical approvals. "
                "Review required."
            )
        else:
            priority = "critical"
            rationale = (
                "Critical failure in schema validation or severe regression in benchmarks. "
                "Immediate human review required."
            )

        return ReviewPriorityOutcome(
            confidence_score=confidence_score,
            review_priority=priority,
            signals=signals,
            rationale=rationale,
        )

    def _evaluate_schema(
        self,
        output: Any,
        schema_def: dict[str, Any] | None,
    ) -> ConfidenceSignal:
        """Evaluate structural conformity against JSON Schema."""
        weight = 0.25
        if not schema_def:
            # If no schema specified, check if output is non-empty
            is_valid = output is not None and str(output).strip() != ""
            return ConfidenceSignal(
                name="schema_validation",
                weight=weight,
                score=1.0 if is_valid else 0.0,
                passed=is_valid,
                details="No formal schema declared; output contains non-empty content.",
            )

        instance = output
        if isinstance(output, str):
            try:
                instance = json.loads(output)
            except json.JSONDecodeError as err:
                return ConfidenceSignal(
                    name="schema_validation",
                    weight=weight,
                    score=0.0,
                    passed=False,
                    details=f"Output is not valid JSON string: {err}",
                )

        try:
            jsonschema.validate(instance=instance, schema=schema_def)
            return ConfidenceSignal(
                name="schema_validation",
                weight=weight,
                score=1.0,
                passed=True,
                details="Output strictly adheres to configured JSON Schema.",
            )
        except jsonschema.ValidationError as err:
            return ConfidenceSignal(
                name="schema_validation",
                weight=weight,
                score=0.0,
                passed=False,
                details=f"Schema validation error: {err.message}",
            )

    def _evaluate_grounding(
        self,
        output: Any,
        input_context: Any | None,
    ) -> ConfidenceSignal:
        """Evaluate keyword citation and grounding overlap with input source."""
        weight = 0.25
        if input_context is None:
            return ConfidenceSignal(
                name="grounding_citation",
                weight=weight,
                score=1.0,
                passed=True,
                details="No source context provided; neutral grounding applied.",
            )

        source_text = (
            json.dumps(input_context) if isinstance(input_context, dict) else str(input_context)
        )
        out_text = json.dumps(output) if isinstance(output, dict) else str(output)

        source_words = set(re.findall(r"\b\w{3,}\b", source_text.lower()))
        out_words = set(re.findall(r"\b\w{3,}\b", out_text.lower()))

        if not out_words:
            return ConfidenceSignal(
                name="grounding_citation",
                weight=weight,
                score=1.0,
                passed=True,
                details="Empty output terms.",
            )

        overlap = out_words.intersection(source_words)
        ratio = round(len(overlap) / len(out_words), 4)
        passed = ratio >= 0.4

        return ConfidenceSignal(
            name="grounding_citation",
            weight=weight,
            score=min(ratio * 2.0, 1.0),  # Scale 50% overlap to 1.0
            passed=passed,
            details=f"Grounding ratio: {ratio:.1%} keyword overlap with input context.",
        )

    async def _evaluate_eval_benchmark(
        self,
        db: AsyncSession,
        agent_id_str: str,
        version_id_str: str | None,
    ) -> ConfidenceSignal:
        """Evaluate latest offline evaluation suite pass rate."""
        weight = 0.25
        try:
            agent_uuid = uuid.UUID(agent_id_str)
        except ValueError:
            return ConfidenceSignal(
                name="eval_benchmark",
                weight=weight,
                score=0.5,
                passed=False,
                details="Invalid agent UUID for eval lookup.",
            )

        query = select(EvalRun).where(
            EvalRun.agent_id == agent_uuid,
            EvalRun.status == "completed",
        )
        if version_id_str:
            try:
                ver_uuid = uuid.UUID(version_id_str)
                query = query.where(EvalRun.agent_version_id == ver_uuid)
            except ValueError:
                pass

        query = query.order_by(EvalRun.created_at.desc()).limit(1)
        res = await db.execute(query)
        latest_run = res.scalars().first()

        if not latest_run or latest_run.pass_rate is None:
            return ConfidenceSignal(
                name="eval_benchmark",
                weight=weight,
                score=0.5,
                passed=False,
                details="No completed offline evaluation runs on record for this version.",
            )

        score = float(latest_run.pass_rate)
        passed = score >= 0.8
        return ConfidenceSignal(
            name="eval_benchmark",
            weight=weight,
            score=score,
            passed=passed,
            details=f"Latest evaluation benchmark pass rate: {score:.1%}.",
        )

    async def _evaluate_approval_history(
        self,
        db: AsyncSession,
        agent_id_str: str,
    ) -> ConfidenceSignal:
        """Evaluate historical human operator approval rate."""
        weight = 0.25
        try:
            agent_uuid = uuid.UUID(agent_id_str)
        except ValueError:
            return ConfidenceSignal(
                name="approval_history",
                weight=weight,
                score=0.7,
                passed=True,
                details="Neutral prior applied.",
            )

        # Count approved vs total resolved approvals for this agent
        total_stmt = select(func.count(Approval.id)).where(
            Approval.agent_id == agent_uuid,
            Approval.status.in_(["approved", "rejected", "edited"]),
        )
        approved_stmt = select(func.count(Approval.id)).where(
            Approval.agent_id == agent_uuid,
            Approval.status == "approved",
        )

        total_res = await db.execute(total_stmt)
        approved_res = await db.execute(approved_stmt)

        total_count = total_res.scalar() or 0
        approved_count = approved_res.scalar() or 0

        if total_count == 0:
            return ConfidenceSignal(
                name="approval_history",
                weight=weight,
                score=0.7,
                passed=True,
                details="No human approval history recorded; neutral prior (70%) applied.",
            )

        ratio = round(approved_count / total_count, 4)
        passed = ratio >= 0.8
        return ConfidenceSignal(
            name="approval_history",
            weight=weight,
            score=ratio,
            passed=passed,
            details=(
                f"Historical human approval rate: {ratio:.1%} "
                f"({approved_count}/{total_count} approved)."
            ),
        )


default_confidence_engine = ReviewPriorityEngine()
