"""Add recovery_codes column to two_factor_secrets

Revision ID: 20251019_add_recovery_codes
Revises: 202502141045_create_user_identities_table
Create Date: 2025-10-19 02:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251019_add_recovery_codes"
down_revision = "202502141045_create_user_identities_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("two_factor_secrets", sa.Column("recovery_codes", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("two_factor_secrets", "recovery_codes")

