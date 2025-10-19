"""add commerce orders and idempotency tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202502170900"
down_revision = "202502141500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commerce_orders",
        sa.Column("order_id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("pv_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_commerce_orders_user_status", "commerce_orders", ["user_id", "status"])
    op.create_index("ix_commerce_orders_created_at", "commerce_orders", ["created_at"])

    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),
    )
    op.create_index("ix_idempotency_keys_status", "idempotency_keys", ["status", "created_at"])
    op.create_index("ix_idempotency_keys_resource", "idempotency_keys", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_resource", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_status", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")

    op.drop_index("ix_commerce_orders_created_at", table_name="commerce_orders")
    op.drop_index("ix_commerce_orders_user_status", table_name="commerce_orders")
    op.drop_table("commerce_orders")
