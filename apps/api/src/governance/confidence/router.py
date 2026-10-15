"""FastAPI router for review-priority and confidence evaluations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, status
from governance.confidence.engine import default_confidence_engine
from governance.confidence.schemas import (
    ConfidenceEvaluationRequest,
    ReviewPriorityOutcome,
)
from shared.db.session import get_db_session

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

DbSession = Annotated["AsyncSession", Depends(get_db_session)]

router = APIRouter(prefix="/api/v1/governance/confidence", tags=["Governance / Confidence"])


@router.post(
    "/evaluate",
    response_model=ReviewPriorityOutcome,
    status_code=status.HTTP_200_OK,
    summary="Evaluate verifiable signals and compute review-priority score",
)
async def evaluate_confidence(
    request: ConfidenceEvaluationRequest,
    db: DbSession,
) -> ReviewPriorityOutcome:
    """Evaluate output against schema, grounding, benchmarks, and approval history."""
    return await default_confidence_engine.evaluate(db, request)
