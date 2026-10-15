"""Governance router combining approval workflows, budget tracking, and evals."""

from __future__ import annotations

from fastapi import APIRouter
from governance.approvals.router import router as approvals_router

router = APIRouter()
router.include_router(approvals_router)
