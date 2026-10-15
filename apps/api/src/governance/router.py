"""Governance router combining approval workflows, budget tracking, and evals."""

from __future__ import annotations

from fastapi import APIRouter
from governance.approvals.router import router as approvals_router
from governance.budgets.router import router as budgets_router
from governance.policies.router import router as policies_router

router = APIRouter()
router.include_router(approvals_router)
router.include_router(budgets_router)
router.include_router(policies_router)
