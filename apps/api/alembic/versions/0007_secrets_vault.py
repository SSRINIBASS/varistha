"""Add secrets table for encrypted vault at rest.

Revision ID: 0007_secrets_vault
Revises: 0006_identity_and_api_keys
Create Date: 2026-10-16 02:15:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0007_secrets_vault"
down_revision: str | None = "0006_identity_and_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create secrets table with encrypted_value storage."""
    op.create_table(
        "secrets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_secrets_name", "secrets", ["name"])


def downgrade() -> None:
    """Drop secrets table and index."""
    op.drop_index("ix_secrets_name", table_name="secrets")
    op.drop_table("secrets")
