"""Add eval_suites, eval_runs, and eval_results tables.

Revision ID: 0005_evals
Revises: 0004_budgets_and_killswitch
Create Date: 2026-10-16 01:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0005_evals"
down_revision: str | None = "0004_budgets_and_killswitch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create eval_suites, eval_runs, and eval_results tables."""
    # 1. eval_suites
    op.create_table(
        "eval_suites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "config",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_eval_suites_name", "eval_suites", ["name"])
    op.create_index("ix_eval_suites_agent_id", "eval_suites", ["agent_id"])

    # 2. eval_runs
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "suite_id",
            sa.Uuid(),
            sa.ForeignKey("eval_suites.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "agent_version_id",
            sa.Uuid(),
            sa.ForeignKey("agent_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("trigger", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("pass_rate", sa.Float(), nullable=True),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_eval_runs_suite_id", "eval_runs", ["suite_id"])
    op.create_index("ix_eval_runs_agent_id", "eval_runs", ["agent_id"])
    op.create_index("ix_eval_runs_agent_version_id", "eval_runs", ["agent_version_id"])
    op.create_index("ix_eval_runs_status", "eval_runs", ["status"])

    # 3. eval_results
    op.create_table(
        "eval_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "eval_run_id",
            sa.Uuid(),
            sa.ForeignKey("eval_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(100), nullable=False),
        sa.Column("case_name", sa.String(255), nullable=False),
        sa.Column(
            "input_data",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "expected_output",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "actual_output",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evaluator_name", sa.String(100), nullable=False),
        sa.Column("evaluator_type", sa.String(50), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_eval_results_eval_run_id", "eval_results", ["eval_run_id"])


def downgrade() -> None:
    """Drop eval_results, eval_runs, and eval_suites tables."""
    op.drop_index("ix_eval_results_eval_run_id", table_name="eval_results")
    op.drop_table("eval_results")

    op.drop_index("ix_eval_runs_status", table_name="eval_runs")
    op.drop_index("ix_eval_runs_agent_version_id", table_name="eval_runs")
    op.drop_index("ix_eval_runs_agent_id", table_name="eval_runs")
    op.drop_index("ix_eval_runs_suite_id", table_name="eval_runs")
    op.drop_table("eval_runs")

    op.drop_index("ix_eval_suites_agent_id", table_name="eval_suites")
    op.drop_index("ix_eval_suites_name", table_name="eval_suites")
    op.drop_table("eval_suites")
