"""create organization and bonus engine tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202502141500"
down_revision = "202502141200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_nodes",
        sa.Column("node_id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("tree_type", sa.String(length=16), nullable=False),
        sa.Column("parent_node_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id"), nullable=True),
        sa.Column("sponsor_user_id", sa.String(length=64), nullable=True),
        sa.Column("position", sa.String(length=8), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("rank", sa.String(length=32), nullable=True),
        sa.Column("center_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_organization_nodes_tree_user", "organization_nodes", ["tree_type", "user_id"], unique=True)
    op.create_index("ix_organization_nodes_parent", "organization_nodes", ["parent_node_id"])
    op.create_index("ix_organization_nodes_sponsor", "organization_nodes", ["sponsor_user_id"])

    op.create_table(
        "organization_closure",
        sa.Column("ancestor_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("descendant_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tree_type", sa.String(length=16), primary_key=True),
        sa.Column("depth", sa.Integer(), nullable=False),
    )
    op.create_index("ix_organization_closure_desc_tree", "organization_closure", ["descendant_id", "tree_type"])

    op.create_table(
        "organization_metrics_daily",
        sa.Column("metric_date", sa.Date(), primary_key=True),
        sa.Column("node_id", sa.String(length=64), primary_key=True),
        sa.Column("tree_type", sa.String(length=16), primary_key=True),
        sa.Column("personal_volume", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("group_volume", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("volume_left", sa.Numeric(18, 4), nullable=True),
        sa.Column("volume_right", sa.Numeric(18, 4), nullable=True),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_org_metrics_node_date", "organization_metrics_daily", ["node_id", "metric_date"])

    op.create_table(
        "organization_rank_history",
        sa.Column("history_id", sa.String(length=64), primary_key=True),
        sa.Column("node_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.String(length=32), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rank_history_node_date", "organization_rank_history", ["node_id", "effective_date"])

    op.create_table(
        "organization_spillover_logs",
        sa.Column("log_id", sa.String(length=64), primary_key=True),
        sa.Column("tree_type", sa.String(length=16), nullable=False),
        sa.Column("sponsor_user_id", sa.String(length=64), nullable=False),
        sa.Column("assigned_user_id", sa.String(length=64), nullable=False),
        sa.Column("parent_node_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_spillover_sponsor_created", "organization_spillover_logs", ["sponsor_user_id", "created_at"])

    op.create_table(
        "binary_slots",
        sa.Column("node_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("slot", sa.String(length=5), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="OPEN"),
        sa.Column("child_node_id", sa.String(length=64), nullable=True),
        sa.Column("last_assigned_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "binary_waiting_queue",
        sa.Column("queue_id", sa.String(length=64), primary_key=True),
        sa.Column("sponsor_node_id", sa.String(length=64), sa.ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_user_id", sa.String(length=64), nullable=False),
        sa.Column("preferred_slot", sa.String(length=5), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enqueued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_binary_queue_status", "binary_waiting_queue", ["status", "enqueued_at"])

    op.create_table(
        "bonus_transactions",
        sa.Column("bonus_id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("source_user_id", sa.String(length=64), nullable=True),
        sa.Column("bonus_type", sa.String(length=32), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("pv_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("bonus_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("hold_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bonus_transactions_order_type", "bonus_transactions", ["order_id", "bonus_type"])
    op.create_index("ix_bonus_transactions_user_status", "bonus_transactions", ["user_id", "status"])

    op.create_table(
        "bonus_daily_closing",
        sa.Column("closing_id", sa.String(length=64), primary_key=True),
        sa.Column("closing_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bonus_daily_closing_date", "bonus_daily_closing", ["closing_date"])

    op.create_table(
        "bonus_retry_queue",
        sa.Column("queue_id", sa.String(length=64), primary_key=True),
        sa.Column("bonus_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("bonus_type", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.String(length=256), nullable=True),
        sa.Column("retry_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bonus_retry_bonus", "bonus_retry_queue", ["bonus_id"])
    op.create_index("ix_bonus_retry_status", "bonus_retry_queue", ["status", "retry_after"])


def downgrade() -> None:
    op.drop_index("ix_bonus_retry_status", table_name="bonus_retry_queue")
    op.drop_index("ix_bonus_retry_bonus", table_name="bonus_retry_queue")
    op.drop_table("bonus_retry_queue")

    op.drop_index("ix_bonus_daily_closing_date", table_name="bonus_daily_closing")
    op.drop_table("bonus_daily_closing")

    op.drop_index("ix_bonus_transactions_user_status", table_name="bonus_transactions")
    op.drop_index("ix_bonus_transactions_order_type", table_name="bonus_transactions")
    op.drop_table("bonus_transactions")

    op.drop_index("ix_binary_queue_status", table_name="binary_waiting_queue")
    op.drop_table("binary_waiting_queue")

    op.drop_table("binary_slots")

    op.drop_index("ix_spillover_sponsor_created", table_name="organization_spillover_logs")
    op.drop_table("organization_spillover_logs")

    op.drop_index("ix_rank_history_node_date", table_name="organization_rank_history")
    op.drop_table("organization_rank_history")

    op.drop_index("ix_org_metrics_node_date", table_name="organization_metrics_daily")
    op.drop_table("organization_metrics_daily")

    op.drop_index("ix_organization_closure_desc_tree", table_name="organization_closure")
    op.drop_table("organization_closure")

    op.drop_index("ix_organization_nodes_sponsor", table_name="organization_nodes")
    op.drop_index("ix_organization_nodes_parent", table_name="organization_nodes")
    op.drop_index("ix_organization_nodes_tree_user", table_name="organization_nodes")
    op.drop_table("organization_nodes")
