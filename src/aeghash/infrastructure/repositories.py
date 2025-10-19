"""SQLAlchemy implementations of Wallet and Mining repositories."""

from __future__ import annotations

from decimal import Decimal
from datetime import UTC, datetime, date
from typing import Any, Mapping, Optional, Sequence

from sqlalchemy import Boolean, Date, DateTime, JSON, Numeric, String, UniqueConstraint, func, ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, Session, mapped_column
from aeghash.core.repositories import (
    LoginAuditRecord,
    LoginAuditRepository,
    MiningBalanceRecord,
    MiningRepository,
    PointLedgerRecord,
    PointWalletRecord,
    PointWalletRepository,
    KnownDeviceRecord,
    RiskEventRecord,
    OrganizationNodeRecord,
    OrganizationRepository,
    OrganizationMetricsRepository,
    OrganizationKpiRecord,
    SpilloverLogRecord,
    RiskRepository,
    BonusEntryRecord,
    BonusRepository,
    BonusRetryRecord,
    OrderRecord,
    OrderRepository,
    IdempotencyKeyRecord,
    IdempotencyRepository,
    SessionRecord,
    SessionRepository,
    TransactionRecord,
    TwoFactorRecord,
    TwoFactorRepository,
    UserAccountRecord,
    UserAccountRepository,
    UserRecord,
    UserRepository,
    WalletRecord,
    WalletRepository,
    WithdrawalAuditRecord,
    WithdrawalAuditRepository,
    WithdrawalRecord,
    WithdrawalRequestRecord,
)
from aeghash.infrastructure.database import Base


class WalletModel(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    address: Mapped[str] = mapped_column(String(128), unique=True)
    wallet_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TransactionModel(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wallet_ref: Mapped[str] = mapped_column(String(128), index=True)
    txid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    coin: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderModel(Base):
    __tablename__ = "commerce_orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    pv_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String(32), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IdempotencyKeyModel(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    scope: Mapped[str] = mapped_column(String(64))
    payload_hash: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16))
    resource_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PointWalletModel(Base):
    __tablename__ = "point_wallets"

    wallet_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    pending_withdrawal: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PointLedgerModel(Base):
    __tablename__ = "point_wallet_ledger"

    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    wallet_id: Mapped[str] = mapped_column(String(64), index=True)
    entry_type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    pending_after: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PointWithdrawalModel(Base):
    __tablename__ = "point_wallet_withdrawals"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    wallet_id: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(32), index=True)
    requested_by: Mapped[str] = mapped_column(String(64))
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rejected_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class WithdrawalAuditModel(Base):
    __tablename__ = "withdrawal_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    wallet_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(32))
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskEventModel(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(String(255))
    attributes: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskKnownDeviceModel(Base):
    __tablename__ = "risk_known_devices"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_risk_device"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    device_id: Mapped[str] = mapped_column(String(128))
    first_seen: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationNodeModel(Base):
    __tablename__ = "organization_nodes"
    __table_args__ = (UniqueConstraint("tree_type", "user_id", name="uq_org_tree_user"),)

    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    tree_type: Mapped[str] = mapped_column(String(16), index=True)
    parent_node_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("organization_nodes.node_id"), nullable=True, index=True)
    sponsor_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    depth: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(String(1024))
    rank: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    center_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationClosureModel(Base):
    __tablename__ = "organization_closure"

    ancestor_id: Mapped[str] = mapped_column(String(64), ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True)
    descendant_id: Mapped[str] = mapped_column(String(64), ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True)
    tree_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    depth: Mapped[int] = mapped_column(Integer)


class OrganizationMetricsDailyModel(Base):
    __tablename__ = "organization_metrics_daily"

    metric_date: Mapped[Date] = mapped_column(Date, primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tree_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    personal_volume: Mapped[Decimal] = mapped_column(Numeric(18, 4), server_default="0")
    group_volume: Mapped[Decimal] = mapped_column(Numeric(18, 4), server_default="0")
    volume_left: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    volume_right: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    orders_count: Mapped[int] = mapped_column(Integer, server_default="0")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OrganizationRankHistoryModel(Base):
    __tablename__ = "organization_rank_history"

    history_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), index=True)
    rank: Mapped[str] = mapped_column(String(32))
    effective_date: Mapped[Date] = mapped_column(Date)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpilloverLogModel(Base):
    __tablename__ = "organization_spillover_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tree_type: Mapped[str] = mapped_column(String(16))
    sponsor_user_id: Mapped[str] = mapped_column(String(64), index=True)
    assigned_user_id: Mapped[str] = mapped_column(String(64))
    parent_node_id: Mapped[str] = mapped_column(String(64))
    position: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BinarySlotModel(Base):
    __tablename__ = "binary_slots"

    node_id: Mapped[str] = mapped_column(String(64), ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), primary_key=True)
    slot: Mapped[str] = mapped_column(String(5), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), server_default="OPEN")
    child_node_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_assigned_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class BinaryWaitingQueueModel(Base):
    __tablename__ = "binary_waiting_queue"

    queue_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sponsor_node_id: Mapped[str] = mapped_column(String(64), ForeignKey("organization_nodes.node_id", ondelete="CASCADE"), index=True)
    candidate_user_id: Mapped[str] = mapped_column(String(64))
    preferred_slot: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    status: Mapped[str] = mapped_column(String(16), server_default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0")
    enqueued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_attempt_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class BonusTransactionModel(Base):
    __tablename__ = "bonus_transactions"

    bonus_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    source_user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bonus_type: Mapped[str] = mapped_column(String(32), index=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pv_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), server_default="0")
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String(16), index=True, server_default="PENDING")
    hold_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


# Backwards-compatibility alias for legacy model naming in tests/migrations.
BonusEntryModel = BonusTransactionModel


class BonusDailyClosingModel(Base):
    __tablename__ = "bonus_daily_closing"

    closing_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    closing_date: Mapped[Date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(16), server_default="PENDING")
    started_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary_json: Mapped[Optional[dict[str, object]]] = mapped_column("summary_json", JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BonusRetryQueueModel(Base):
    __tablename__ = "bonus_retry_queue"

    queue_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bonus_id: Mapped[str] = mapped_column(String(64), index=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    bonus_type: Mapped[str] = mapped_column(String(32))
    failure_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    retry_after: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0")
    status: Mapped[str] = mapped_column(String(16), server_default="PENDING")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class MiningBalanceModel(Base):
    __tablename__ = "mining_balances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    credit: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    power: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    date: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WithdrawalModel(Base):
    __tablename__ = "mining_withdrawals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    withdraw_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    coin: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginAuditModel(Base):
    __tablename__ = "login_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TwoFactorModel(Base):
    __tablename__ = "two_factor_secrets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    secret: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column()
    recovery_codes: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuthSessionModel(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    roles: Mapped[str] = mapped_column(String(256))
    expires_at: Mapped[Numeric] = mapped_column(Numeric(18, 3))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserIdentityModel(Base):
    __tablename__ = "user_identities"
    __table_args__ = (UniqueConstraint("provider", "subject", name="uq_user_identity_provider_subject"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    subject: Mapped[str] = mapped_column(String(128))
    roles: Mapped[str] = mapped_column(String(256))
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserAccountModel(Base):
    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy-backed repository for commerce orders."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_order(self, order_id: str) -> Optional[OrderRecord]:
        model = self._session.get(OrderModel, order_id)
        if model is None:
            return None
        return self._map_order(model)

    def upsert_order(self, record: OrderRecord) -> OrderRecord:
        model = self._session.get(OrderModel, record.order_id)
        if model is None:
            model = OrderModel(
                order_id=record.order_id,
                user_id=record.user_id,
                total_amount=record.total_amount,
                pv_amount=record.pv_amount,
                status=record.status,
                channel=record.channel,
                metadata_json=dict(record.metadata),
                created_at=record.created_at,
            )
            self._session.add(model)
        else:
            model.user_id = record.user_id
            model.total_amount = record.total_amount
            model.pv_amount = record.pv_amount
            model.status = record.status
            model.channel = record.channel
            model.metadata_json = dict(record.metadata)
            model.created_at = record.created_at
        return self._map_order(model)

    def _map_order(self, model: OrderModel) -> OrderRecord:
        return OrderRecord(
            order_id=model.order_id,
            user_id=model.user_id,
            total_amount=Decimal(model.total_amount),
            pv_amount=Decimal(model.pv_amount),
            status=model.status,
            channel=model.channel,
            metadata=model.metadata_json or {},
            created_at=model.created_at or datetime.now(UTC),
        )


class SqlAlchemyIdempotencyRepository(IdempotencyRepository):
    """SQLAlchemy-backed idempotency key repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, record: IdempotencyKeyRecord) -> bool:
        existing = (
            self._session.query(IdempotencyKeyModel)
            .filter(
                IdempotencyKeyModel.scope == record.scope,
                IdempotencyKeyModel.key == record.key,
            )
            .one_or_none()
        )
        if existing:
            return False
        model = IdempotencyKeyModel(
            key=record.key,
            scope=record.scope,
            payload_hash=record.payload_hash,
            status=record.status,
            resource_id=record.resource_id,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )
        self._session.add(model)
        return True

    def get(self, *, key: str, scope: str) -> Optional[IdempotencyKeyRecord]:
        model = (
            self._session.query(IdempotencyKeyModel)
            .filter(
                IdempotencyKeyModel.scope == scope,
                IdempotencyKeyModel.key == key,
            )
            .one_or_none()
        )
        if model is None:
            return None
        return self._map_idempotency(model)

    def mark_status(self, *, key: str, scope: str, status: str, resource_id: Optional[str] = None) -> None:
        query = (
            self._session.query(IdempotencyKeyModel)
            .filter(
                IdempotencyKeyModel.scope == scope,
                IdempotencyKeyModel.key == key,
            )
        )
        updates: dict[str, Any] = {"status": status}
        if resource_id is not None:
            updates["resource_id"] = resource_id
        query.update(updates)

    def _map_idempotency(self, model: IdempotencyKeyModel) -> IdempotencyKeyRecord:
        return IdempotencyKeyRecord(
            key=model.key,
            scope=model.scope,
            payload_hash=model.payload_hash,
            status=model.status,
            created_at=model.created_at or datetime.now(UTC),
            expires_at=model.expires_at,
            resource_id=model.resource_id,
        )


class SqlAlchemyWalletRepository(WalletRepository):
    """SQLAlchemy-backed wallet repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_wallet(self, wallet: WalletRecord) -> None:
        model = WalletModel(user_id=wallet.user_id, address=wallet.address, wallet_key=wallet.wallet_key)
        self._session.add(model)
        self._session.flush()

    def log_transaction(self, transaction: TransactionRecord) -> None:
        model = TransactionModel(
            wallet_ref=transaction.wallet_id,
            txid=transaction.txid,
            amount=transaction.amount,
            coin=transaction.coin,
            status=transaction.status,
        )
        self._session.add(model)


class SqlAlchemyPointWalletRepository(PointWalletRepository):
    """SQLAlchemy-backed repository for point wallets and withdrawals."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_wallet(self, wallet_id: str) -> Optional[PointWalletRecord]:
        model = self._session.query(PointWalletModel).filter(PointWalletModel.wallet_id == wallet_id).one_or_none()
        return self._map_wallet(model)

    def get_wallet_by_user(self, user_id: str) -> Optional[PointWalletRecord]:
        model = self._session.query(PointWalletModel).filter(PointWalletModel.user_id == user_id).one_or_none()
        return self._map_wallet(model)

    def create_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        model = PointWalletModel(
            wallet_id=record.wallet_id,
            user_id=record.user_id,
            balance=record.balance,
            pending_withdrawal=record.pending_withdrawal,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        self._session.add(model)
        self._session.flush()
        return self._map_wallet(model)  # type: ignore[arg-type]

    def update_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        model = self._session.query(PointWalletModel).filter(PointWalletModel.wallet_id == record.wallet_id).one()
        model.user_id = record.user_id
        model.balance = record.balance
        model.pending_withdrawal = record.pending_withdrawal
        model.status = record.status
        model.updated_at = record.updated_at
        self._session.flush()
        return self._map_wallet(model)

    def add_ledger_entry(self, entry: PointLedgerRecord) -> None:
        model = PointLedgerModel(
            entry_id=entry.entry_id,
            wallet_id=entry.wallet_id,
            entry_type=entry.entry_type,
            amount=entry.amount,
            balance_after=entry.balance_after,
            pending_after=entry.pending_after,
            reference_id=entry.reference_id,
            metadata_json=dict(entry.metadata) if entry.metadata is not None else None,
            created_at=entry.created_at,
        )
        self._session.add(model)

    def get_withdrawal_request(self, request_id: str) -> Optional[WithdrawalRequestRecord]:
        model = (
            self._session.query(PointWithdrawalModel)
            .filter(PointWithdrawalModel.request_id == request_id)
            .one_or_none()
        )
        return self._map_withdrawal(model)

    def create_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        model = PointWithdrawalModel(
            request_id=record.request_id,
            wallet_id=record.wallet_id,
            amount=record.amount,
            status=record.status,
            requested_by=record.requested_by,
            reference_id=record.reference_id,
            metadata_json=dict(record.metadata) if record.metadata is not None else None,
            created_at=record.created_at,
            approved_by=record.approved_by,
            approved_at=record.approved_at,
            rejected_by=record.rejected_by,
            rejected_at=record.rejected_at,
            notes=record.notes,
        )
        self._session.add(model)
        self._session.flush()
        return self._map_withdrawal(model)

    def update_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        model = (
            self._session.query(PointWithdrawalModel)
            .filter(PointWithdrawalModel.request_id == record.request_id)
            .one()
        )
        model.status = record.status
        model.approved_by = record.approved_by
        model.approved_at = record.approved_at
        model.rejected_by = record.rejected_by
        model.rejected_at = record.rejected_at
        model.notes = record.notes
        model.metadata_json = dict(record.metadata) if record.metadata is not None else None
        self._session.flush()
        return self._map_withdrawal(model)

    def list_withdrawal_requests(
        self,
        *,
        wallet_id: str,
        statuses: Sequence[str] | None = None,
    ) -> Sequence[WithdrawalRequestRecord]:
        query = self._session.query(PointWithdrawalModel).filter(PointWithdrawalModel.wallet_id == wallet_id)
        if statuses:
            query = query.filter(PointWithdrawalModel.status.in_(list(statuses)))
        models = query.order_by(PointWithdrawalModel.created_at.asc()).all()
        return [self._map_withdrawal(model) for model in models]

    def _map_wallet(self, model: PointWalletModel | None) -> Optional[PointWalletRecord]:
        if not model:
            return None
        created_at = model.created_at or datetime.now(UTC)
        updated_at = model.updated_at or created_at
        return PointWalletRecord(
            wallet_id=model.wallet_id,
            user_id=model.user_id,
            balance=Decimal(model.balance),
            pending_withdrawal=Decimal(model.pending_withdrawal),
            status=model.status,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _map_withdrawal(self, model: PointWithdrawalModel | None) -> Optional[WithdrawalRequestRecord]:
        if not model:
            return None
        metadata = model.metadata_json if model.metadata_json is None else dict(model.metadata_json)
        return WithdrawalRequestRecord(
            request_id=model.request_id,
            wallet_id=model.wallet_id,
            amount=Decimal(model.amount),
            status=model.status,
            requested_by=model.requested_by,
            reference_id=model.reference_id,
            metadata=metadata,
            created_at=model.created_at or datetime.now(UTC),
            approved_by=model.approved_by,
            approved_at=model.approved_at,
            rejected_by=model.rejected_by,
            rejected_at=model.rejected_at,
            notes=model.notes,
        )


class SqlAlchemyWithdrawalAuditRepository(WithdrawalAuditRepository):
    """SQLAlchemy-backed repository for withdrawal audit logs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log(self, record: WithdrawalAuditRecord) -> None:
        model = WithdrawalAuditModel(
            request_id=record.request_id,
            wallet_id=record.wallet_id,
            action=record.action,
            actor_id=record.actor_id,
            amount=record.amount,
            status=record.status,
            notes=record.notes,
            metadata_json=dict(record.metadata) if record.metadata is not None else None,
            created_at=record.created_at,
        )
        self._session.add(model)

    def list_for_request(self, request_id: str, *, limit: int = 100) -> Sequence[WithdrawalAuditRecord]:
        query = (
            self._session.query(WithdrawalAuditModel)
            .filter(WithdrawalAuditModel.request_id == request_id)
            .order_by(WithdrawalAuditModel.created_at.asc(), WithdrawalAuditModel.id.asc())
            .limit(limit)
        )
        results: list[WithdrawalAuditRecord] = []
        for model in query:
            metadata = model.metadata_json if model.metadata_json is None else dict(model.metadata_json)
            results.append(
                WithdrawalAuditRecord(
                    request_id=model.request_id,
                    wallet_id=model.wallet_id,
                    action=model.action,
                    actor_id=model.actor_id,
                    amount=Decimal(model.amount),
                    status=model.status,
                    notes=model.notes,
                    metadata=metadata,
                    created_at=model.created_at or datetime.now(UTC),
                ),
            )
        return results


class SqlAlchemyRiskRepository(RiskRepository):
    """SQLAlchemy-backed repository for risk events and known devices."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record_event(self, record: RiskEventRecord) -> None:
        model = RiskEventModel(
            event_id=record.event_id,
            user_id=record.user_id,
            category=record.category,
            severity=record.severity,
            message=record.message,
            attributes=dict(record.attributes),
            created_at=record.created_at,
        )
        self._session.add(model)

    def list_recent(self, user_id: str, *, limit: int = 50) -> Sequence[RiskEventRecord]:
        query = (
            self._session.query(RiskEventModel)
            .filter(RiskEventModel.user_id == user_id)
            .order_by(RiskEventModel.created_at.desc(), RiskEventModel.id.desc())
            .limit(limit)
        )
        results: list[RiskEventRecord] = []
        for model in query:
            attrs = model.attributes if model.attributes is None else dict(model.attributes)
            results.append(
                RiskEventRecord(
                    event_id=model.event_id,
                    user_id=model.user_id,
                    category=model.category,
                    severity=model.severity,
                    message=model.message,
                    attributes=attrs or {},
                    created_at=model.created_at or datetime.now(UTC),
                ),
            )
        return results

    def get_known_device(self, user_id: str, device_id: str) -> Optional[KnownDeviceRecord]:
        model = (
            self._session.query(RiskKnownDeviceModel)
            .filter(
                RiskKnownDeviceModel.user_id == user_id,
                RiskKnownDeviceModel.device_id == device_id,
            )
            .one_or_none()
        )
        if not model:
            return None
        return KnownDeviceRecord(
            user_id=model.user_id,
            device_id=model.device_id,
            first_seen=model.first_seen or datetime.now(UTC),
            last_seen=model.last_seen or datetime.now(UTC),
        )

    def upsert_known_device(self, record: KnownDeviceRecord) -> None:
        existing = (
            self._session.query(RiskKnownDeviceModel)
            .filter(
                RiskKnownDeviceModel.user_id == record.user_id,
                RiskKnownDeviceModel.device_id == record.device_id,
            )
            .one_or_none()
        )
        if existing:
            existing.last_seen = record.last_seen
        else:
            self._session.add(
                RiskKnownDeviceModel(
                    user_id=record.user_id,
                    device_id=record.device_id,
                    first_seen=record.first_seen,
                    last_seen=record.last_seen,
                ),
            )


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    """SQLAlchemy-backed repository for organization nodes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_node(self, record: OrganizationNodeRecord) -> OrganizationNodeRecord:
        model = OrganizationNodeModel(
            node_id=record.node_id,
            user_id=record.user_id,
            tree_type=record.tree_type,
            parent_node_id=record.parent_node_id,
            sponsor_user_id=record.sponsor_user_id,
            position=record.position,
            depth=record.depth,
            path=record.path,
            rank=record.rank,
            center_id=record.center_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        self._session.add(model)
        self._session.flush()

        self._ensure_closure_entries(record)

        if record.tree_type == "binary":
            self._ensure_binary_slots(record.node_id)
            if record.parent_node_id and record.position:
                self._fill_binary_slot(record.parent_node_id, record.position, record.node_id)

        return self._map_node(model)

    def get_node(self, node_id: str) -> Optional[OrganizationNodeRecord]:
        model = self._session.query(OrganizationNodeModel).filter(OrganizationNodeModel.node_id == node_id).one_or_none()
        return self._map_node(model)

    def get_node_by_user(self, tree_type: str, user_id: str) -> Optional[OrganizationNodeRecord]:
        model = (
            self._session.query(OrganizationNodeModel)
            .filter(
                OrganizationNodeModel.tree_type == tree_type,
                OrganizationNodeModel.user_id == user_id,
            )
            .one_or_none()
        )
        return self._map_node(model)

    def list_children(self, node_id: str) -> Sequence[OrganizationNodeRecord]:
        models = (
            self._session.query(OrganizationNodeModel)
            .filter(OrganizationNodeModel.parent_node_id == node_id)
            .order_by(OrganizationNodeModel.position.asc())
            .all()
        )
        return [self._map_node(model) for model in models]

    def log_spillover(self, record: SpilloverLogRecord) -> None:
        self._session.add(
            SpilloverLogModel(
                log_id=record.log_id,
                tree_type=record.tree_type,
                sponsor_user_id=record.sponsor_user_id,
                assigned_user_id=record.assigned_user_id,
                parent_node_id=record.parent_node_id,
                position=record.position,
                created_at=record.created_at,
            ),
        )

    def list_spillovers(self, sponsor_user_id: str, *, limit: int = 100) -> Sequence[SpilloverLogRecord]:
        query = (
            self._session.query(SpilloverLogModel)
            .filter(SpilloverLogModel.sponsor_user_id == sponsor_user_id)
            .order_by(SpilloverLogModel.created_at.desc(), SpilloverLogModel.log_id.desc())
            .limit(limit)
        )
        return [
            SpilloverLogRecord(
                log_id=model.log_id,
                tree_type=model.tree_type,
                sponsor_user_id=model.sponsor_user_id,
                assigned_user_id=model.assigned_user_id,
                parent_node_id=model.parent_node_id,
                position=model.position,
                created_at=model.created_at or datetime.now(UTC),
            )
            for model in query
        ]

    def _map_node(self, model: OrganizationNodeModel | None) -> Optional[OrganizationNodeRecord]:
        if not model:
            return None
        return OrganizationNodeRecord(
            node_id=model.node_id,
            user_id=model.user_id,
            tree_type=model.tree_type,
            parent_node_id=model.parent_node_id,
            sponsor_user_id=model.sponsor_user_id,
            position=model.position,
            depth=model.depth,
            path=model.path,
            created_at=model.created_at or datetime.now(UTC),
            updated_at=model.updated_at or datetime.now(UTC),
            rank=model.rank,
            center_id=model.center_id,
        )

    def get_nodes_by_ids(self, node_ids: Sequence[str]) -> Sequence[OrganizationNodeRecord]:
        if not node_ids:
            return []
        models = (
            self._session.query(OrganizationNodeModel)
            .filter(OrganizationNodeModel.node_id.in_(list(node_ids)))
            .all()
        )
        lookup = {model.node_id: self._map_node(model) for model in models}
        return [lookup[node_id] for node_id in node_ids if node_id in lookup]

    def is_descendant(self, *, ancestor_node_id: str, descendant_node_id: str, tree_type: str) -> bool:
        count = (
            self._session.query(OrganizationClosureModel)
            .filter(
                OrganizationClosureModel.ancestor_id == ancestor_node_id,
                OrganizationClosureModel.descendant_id == descendant_node_id,
                OrganizationClosureModel.tree_type == tree_type,
            )
            .count()
        )
        return count > 0

    def _ensure_closure_entries(self, record: OrganizationNodeRecord) -> None:
        existing = (
            self._session.query(OrganizationClosureModel)
            .filter(
                OrganizationClosureModel.descendant_id == record.node_id,
                OrganizationClosureModel.tree_type == record.tree_type,
            )
            .count()
        )
        if existing:
            return

        # self reference
        self._session.add(
            OrganizationClosureModel(
                ancestor_id=record.node_id,
                descendant_id=record.node_id,
                tree_type=record.tree_type,
                depth=0,
            ),
        )

        if record.parent_node_id:
            parent_closures = (
                self._session.query(OrganizationClosureModel)
                .filter(
                    OrganizationClosureModel.descendant_id == record.parent_node_id,
                    OrganizationClosureModel.tree_type == record.tree_type,
                )
                .all()
            )
            for closure in parent_closures:
                self._session.add(
                    OrganizationClosureModel(
                        ancestor_id=closure.ancestor_id,
                        descendant_id=record.node_id,
                        tree_type=record.tree_type,
                        depth=closure.depth + 1,
                    ),
                )

    def _ensure_binary_slots(self, node_id: str) -> None:
        existing = {
            slot.slot
            for slot in self._session.query(BinarySlotModel).filter(BinarySlotModel.node_id == node_id)
        }
        for slot_name in ("L", "R"):
            if slot_name not in existing:
                self._session.add(
                    BinarySlotModel(
                        node_id=node_id,
                        slot=slot_name,
                        status="OPEN",
                        last_assigned_at=None,
                    ),
                )

    def _fill_binary_slot(self, parent_node_id: str, slot: str, child_node_id: str) -> None:
        slot = slot.upper()
        slot_model = (
            self._session.query(BinarySlotModel)
            .filter(
                BinarySlotModel.node_id == parent_node_id,
                BinarySlotModel.slot == slot,
            )
            .one_or_none()
        )
        now = datetime.now(UTC)
        if slot_model:
            slot_model.status = "FILLED"
            slot_model.child_node_id = child_node_id
            slot_model.last_assigned_at = now
        else:
            self._session.add(
                BinarySlotModel(
                    node_id=parent_node_id,
                    slot=slot,
                    status="FILLED",
                    child_node_id=child_node_id,
                    last_assigned_at=now,
                ),
            )


class SqlAlchemyOrganizationMetricsRepository(OrganizationMetricsRepository):
    """SQLAlchemy-backed repository for organization KPI metrics."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_metrics(
        self,
        node_id: str,
        *,
        tree_type: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[OrganizationKpiRecord]:
        query = (
            self._session.query(OrganizationMetricsDailyModel)
            .filter(OrganizationMetricsDailyModel.node_id == node_id)
            .filter(OrganizationMetricsDailyModel.tree_type == tree_type)
            .filter(OrganizationMetricsDailyModel.metric_date >= start_date)
            .filter(OrganizationMetricsDailyModel.metric_date <= end_date)
            .order_by(OrganizationMetricsDailyModel.metric_date.asc())
        )
        return [
            OrganizationKpiRecord(
                node_id=model.node_id,
                tree_type=model.tree_type,
                metric_date=model.metric_date,
                personal_volume=Decimal(model.personal_volume or 0),
                group_volume=Decimal(model.group_volume or 0),
                volume_left=Decimal(model.volume_left) if model.volume_left is not None else None,
                volume_right=Decimal(model.volume_right) if model.volume_right is not None else None,
                orders_count=model.orders_count,
            )
            for model in query
        ]


class SqlAlchemyBonusRepository(BonusRepository):
    """SQLAlchemy-backed repository for bonus entries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record_bonus(self, record: BonusEntryRecord) -> None:
        model = BonusTransactionModel(
            bonus_id=record.bonus_id,
            user_id=record.user_id,
            source_user_id=record.source_user_id,
            bonus_type=record.bonus_type,
            order_id=record.order_id,
            level=record.level,
            pv_amount=record.pv_amount,
            bonus_amount=record.bonus_amount,
            status=record.status,
            hold_until=record.hold_until,
            metadata_json=dict(record.metadata),
            created_at=record.created_at,
            confirmed_at=record.confirmed_at,
        )
        self._session.add(model)

    def list_pending(self, *, limit: int = 100) -> Sequence[BonusEntryRecord]:
        query = (
            self._session.query(BonusTransactionModel)
            .filter(BonusTransactionModel.status == "PENDING")
            .order_by(BonusTransactionModel.created_at.asc())
            .limit(limit)
        )
        return [
            self._map_bonus(model)
            for model in query
        ]

    def mark_confirmed(self, bonus_id: str) -> None:
        now = datetime.now(UTC)
        self._session.query(BonusTransactionModel).filter(BonusTransactionModel.bonus_id == bonus_id).update({
            "status": "CONFIRMED",
            "confirmed_at": now,
        })
        self._session.query(BonusRetryQueueModel).filter(BonusRetryQueueModel.bonus_id == bonus_id).update({
            "status": "COMPLETED",
            "updated_at": now,
        })

    def schedule_retry(self, bonus_id: str, retry_after: datetime, metadata: Mapping[str, Any]) -> None:
        txn = (
            self._session.query(BonusTransactionModel)
            .filter(BonusTransactionModel.bonus_id == bonus_id)
            .one_or_none()
        )
        if txn is None:
            return

        txn.status = "RETRY"
        txn.metadata_json = dict(metadata)
        txn.hold_until = retry_after

        queue_id = f"retry-{bonus_id}"
        failure_reason = metadata.get("last_error") or metadata.get("reason")
        retry_count = int(metadata.get("retry_count", 0))
        now = datetime.now(UTC)
        queue_model = (
            self._session.query(BonusRetryQueueModel)
            .filter(BonusRetryQueueModel.queue_id == queue_id)
            .one_or_none()
        )
        if queue_model:
            queue_model.order_id = txn.order_id
            queue_model.bonus_type = txn.bonus_type
            queue_model.failure_reason = failure_reason
            queue_model.retry_after = retry_after
            if retry_count:
                queue_model.retry_count = retry_count
            queue_model.status = "PENDING"
            queue_model.updated_at = now
        else:
            self._session.add(
                BonusRetryQueueModel(
                    queue_id=queue_id,
                    bonus_id=bonus_id,
                    order_id=txn.order_id,
                    bonus_type=txn.bonus_type,
                    failure_reason=failure_reason,
                    retry_after=retry_after,
                    retry_count=retry_count,
                    status="PENDING",
                    created_at=now,
                    updated_at=now,
                ),
            )

    def mark_failed(self, bonus_id: str, metadata: Mapping[str, Any]) -> None:
        failure_reason = metadata.get("last_error") or metadata.get("reason")
        now = datetime.now(UTC)
        self._session.query(BonusTransactionModel).filter(BonusTransactionModel.bonus_id == bonus_id).update({
            "status": "FAILED",
            "metadata_json": dict(metadata),
        })
        self._session.query(BonusRetryQueueModel).filter(BonusRetryQueueModel.bonus_id == bonus_id).update({
            "status": "FAILED",
            "failure_reason": failure_reason,
            "updated_at": now,
        })

    def _map_bonus(self, model: BonusTransactionModel) -> BonusEntryRecord:
        return BonusEntryRecord(
            bonus_id=model.bonus_id,
            user_id=model.user_id,
            source_user_id=model.source_user_id,
            bonus_type=model.bonus_type,
            order_id=model.order_id,
            level=model.level or 0,
            pv_amount=Decimal(model.pv_amount),
            bonus_amount=Decimal(model.bonus_amount),
            status=model.status,
            metadata=model.metadata_json or {},
            created_at=model.created_at or datetime.now(UTC),
            hold_until=model.hold_until,
            confirmed_at=model.confirmed_at,
        )

    def get_entry(self, bonus_id: str) -> Optional[BonusEntryRecord]:
        model = (
            self._session.query(BonusTransactionModel)
            .filter(BonusTransactionModel.bonus_id == bonus_id)
            .one_or_none()
        )
        if model is None:
            return None
        return self._map_bonus(model)

    def list_retry_candidates(self, *, now: datetime, limit: int = 100) -> Sequence[BonusRetryRecord]:
        query = (
            self._session.query(BonusRetryQueueModel)
            .filter(BonusRetryQueueModel.status == "PENDING")
            .filter(
                (BonusRetryQueueModel.retry_after == None)  # noqa: E711
                | (BonusRetryQueueModel.retry_after <= now)
            )
            .order_by(BonusRetryQueueModel.retry_after.asc())
            .limit(limit)
        )
        return [self._map_retry(model) for model in query]

    def mark_retry_started(self, queue_id: str, *, started_at: datetime) -> None:
        self._session.query(BonusRetryQueueModel).filter(BonusRetryQueueModel.queue_id == queue_id).update({
            "status": "PROCESSING",
            "updated_at": started_at,
        })

    def mark_retry_completed(self, queue_id: str, *, completed_at: datetime) -> None:
        self._session.query(BonusRetryQueueModel).filter(BonusRetryQueueModel.queue_id == queue_id).update({
            "status": "COMPLETED",
            "updated_at": completed_at,
        })

    def mark_retry_failed(self, queue_id: str, *, failed_at: datetime, metadata: Mapping[str, Any]) -> None:
        failure_reason = metadata.get("last_error") or metadata.get("reason")
        self._session.query(BonusRetryQueueModel).filter(BonusRetryQueueModel.queue_id == queue_id).update({
            "status": "FAILED",
            "failure_reason": failure_reason,
            "updated_at": failed_at,
        })

    def _map_retry(self, model: BonusRetryQueueModel) -> BonusRetryRecord:
        return BonusRetryRecord(
            queue_id=model.queue_id,
            bonus_id=model.bonus_id,
            order_id=model.order_id,
            bonus_type=model.bonus_type,
            failure_reason=model.failure_reason,
            retry_after=model.retry_after,
            retry_count=model.retry_count,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

class SqlAlchemyMiningRepository(MiningRepository):
    """SQLAlchemy-backed mining repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_balance(self, record: MiningBalanceRecord) -> None:
        existing = (
            self._session.query(MiningBalanceModel).filter(MiningBalanceModel.user_id == record.user_id).one_or_none()
        )
        if existing:
            existing.credit = record.balance.credit
            existing.power = record.balance.power
            existing.date = record.balance.date
        else:
            self._session.add(
                MiningBalanceModel(
                    user_id=record.user_id,
                    credit=record.balance.credit,
                    power=record.balance.power,
                    date=record.balance.date,
                ),
            )

    def log_withdrawal(self, record: WithdrawalRecord) -> None:
        self._session.add(
            WithdrawalModel(
                user_id=record.user_id,
                withdraw_id=record.withdraw_id,
                coin=record.coin,
                amount=record.amount,
                status=record.status,
            ),
        )


class SqlAlchemyLoginAuditRepository(LoginAuditRepository):
    """SQLAlchemy-backed login audit repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log(self, record: LoginAuditRecord) -> None:
        self._session.add(
            LoginAuditModel(
                provider=record.provider,
                status=record.status,
                subject=record.subject,
                reason=record.reason,
            ),
        )

    def list_recent(self, *, limit: int = 100) -> list[LoginAuditRecord]:
        models = (
            self._session.query(LoginAuditModel)
            .order_by(LoginAuditModel.created_at.desc(), LoginAuditModel.id.desc())
            .limit(limit)
            .all()
        )
        return [
            LoginAuditRecord(
                provider=model.provider,
                status=model.status,
                subject=model.subject,
                reason=model.reason,
            )
            for model in models
        ]


class SqlAlchemyTwoFactorRepository(TwoFactorRepository):
    """SQLAlchemy-backed two-factor repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> Optional[TwoFactorRecord]:
        model = self._session.query(TwoFactorModel).filter(TwoFactorModel.user_id == user_id).one_or_none()
        if not model:
            return None
        return TwoFactorRecord(
            user_id=model.user_id,
            secret=model.secret,
            enabled=model.enabled,
            updated_at=model.updated_at.timestamp() if model.updated_at else 0.0,
            recovery_codes=tuple(model.recovery_codes or []),
        )

    def save(self, record: TwoFactorRecord) -> None:
        existing = self._session.query(TwoFactorModel).filter(TwoFactorModel.user_id == record.user_id).one_or_none()
        if existing:
            existing.secret = record.secret
            existing.enabled = record.enabled
            existing.recovery_codes = list(record.recovery_codes)
        else:
            self._session.add(
                TwoFactorModel(
                    user_id=record.user_id,
                    secret=record.secret,
                    enabled=record.enabled,
                    recovery_codes=list(record.recovery_codes),
                ),
            )

    def disable(self, user_id: str) -> None:
        existing = self._session.query(TwoFactorModel).filter(TwoFactorModel.user_id == user_id).one_or_none()
        if existing:
            existing.enabled = False
            existing.recovery_codes = []


class SqlAlchemySessionRepository(SessionRepository):
    """SQLAlchemy-backed session repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_session(self, record: SessionRecord) -> SessionRecord:
        self._session.add(
            AuthSessionModel(
                token=record.token,
                user_id=record.user_id,
                roles=",".join(record.roles),
                expires_at=record.expires_at,
            ),
        )
        return record

    def get_session(self, token: str) -> Optional[SessionRecord]:
        model = self._session.query(AuthSessionModel).filter(AuthSessionModel.token == token).one_or_none()
        if not model:
            return None
        roles = tuple(role for role in model.roles.split(",") if role)
        expires_at = float(model.expires_at) if model.expires_at is not None else 0.0
        return SessionRecord(
            token=model.token,
            user_id=model.user_id,
            roles=roles,
            expires_at=expires_at,
        )


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy-backed user repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_oauth_identity(self, provider: str, subject: str) -> UserRecord | None:
        model = (
            self._session.query(UserIdentityModel)
            .filter(UserIdentityModel.provider == provider, UserIdentityModel.subject == subject)
            .one_or_none()
        )
        if not model:
            return None
        roles = tuple(role for role in model.roles.split(",") if role)
        return UserRecord(
            user_id=model.user_id,
            provider=model.provider,
            subject=model.subject,
            roles=roles,
            two_factor_enabled=bool(model.two_factor_enabled),
        )

    def create_identity(self, record: UserRecord) -> None:
        roles = ",".join(record.roles)
        self._session.add(
            UserIdentityModel(
                user_id=record.user_id,
                provider=record.provider,
                subject=record.subject,
                roles=roles,
                two_factor_enabled=record.two_factor_enabled,
            ),
        )


class SqlAlchemyUserAccountRepository(UserAccountRepository):
    """SQLAlchemy-backed user account repository for local signups."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, record: UserAccountRecord) -> None:
        model = self._session.query(UserAccountModel).filter(UserAccountModel.user_id == record.user_id).one_or_none()
        if model:
            model.email = record.email
            model.password_hash = record.password_hash
            model.is_active = record.is_active
        else:
            self._session.add(
                UserAccountModel(
                    user_id=record.user_id,
                    email=record.email,
                    password_hash=record.password_hash,
                    is_active=record.is_active,
                    created_at=record.created_at,
                ),
            )

    def find_by_email(self, email: str) -> Optional[UserAccountRecord]:
        model = self._session.query(UserAccountModel).filter(UserAccountModel.email == email).one_or_none()
        return self._map(model)

    def find(self, user_id: str) -> Optional[UserAccountRecord]:
        model = self._session.query(UserAccountModel).filter(UserAccountModel.user_id == user_id).one_or_none()
        return self._map(model)

    def _map(self, model: UserAccountModel | None) -> Optional[UserAccountRecord]:
        if not model:
            return None
        created_at = model.created_at
        if created_at is None:  # pragma: no cover - fallback when server default not populated yet
            created_at = datetime.now(UTC)
        return UserAccountRecord(
            user_id=model.user_id,
            email=model.email,
            password_hash=model.password_hash,
            is_active=bool(model.is_active),
            created_at=created_at,
        )
