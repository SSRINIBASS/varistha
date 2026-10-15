"""Add budget tracking and kill switch circuit breaker support.

Revision ID: 0004_budgets_and_killswitch
Revises: 0003_approvals
Create Date: 2026-10-15 18:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0004_budgets_and_killswitch"
down_revision: str | None = "0003_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add kill switch columns to agents and create system_settings table."""
    with op.batch_alter_table("agents") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "kill_switch_tripped",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "kill_switch_reason",
                sa.Text(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "kill_switch_tripped_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column(
            "value",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Revert kill switch columns and drop system_settings table."""
    op.drop_table("system_settings")
    with op.batch_alter_table("agents") as batch_op:
        batch_op.drop_column("kill_switch_tripped_at")
        batch_op.drop_column("kill_switch_reason")
        batch_op.drop_column("kill_switch_tripped")
        batch_op.drop_column("is_active")
