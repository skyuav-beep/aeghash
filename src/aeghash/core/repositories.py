"""Repository protocols and DTOs for core services."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Mapping, Optional, Protocol, Sequence

from aeghash.adapters.hashdam import HashBalance


@dataclass(slots=True)
class WalletRecord:
    user_id: str
    address: str
    wallet_key: str


@dataclass(slots=True)
class TransactionRecord:
    wallet_id: str
    txid: Optional[str]
    amount: Decimal
    coin: str | None
    status: str


@dataclass(slots=True)
class MiningBalanceRecord:
    user_id: str
    balance: HashBalance


@dataclass(slots=True)
class WithdrawalRecord:
    user_id: str
    withdraw_id: Optional[str]
    coin: str
    amount: Decimal
    status: str


@dataclass(slots=True)
class PointWalletRecord:
    """Stored state for an internal point wallet."""

    wallet_id: str
    user_id: str
    balance: Decimal
    pending_withdrawal: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class PointLedgerRecord:
    """Immutable ledger entry capturing wallet balance transitions."""

    entry_id: str
    wallet_id: str
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    pending_after: Decimal
    reference_id: Optional[str]
    metadata: Optional[Mapping[str, Any]]
    created_at: datetime


@dataclass(slots=True)
class WithdrawalRequestRecord:
    """Pending withdrawal request awaiting approval."""

    request_id: str
    wallet_id: str
    amount: Decimal
    status: str
    requested_by: str
    reference_id: Optional[str]
    metadata: Optional[Mapping[str, Any]]
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class WithdrawalAuditRecord:
    """Audit trail entry for withdrawal workflow actions."""

    request_id: str
    wallet_id: str
    action: str
    actor_id: str
    amount: Decimal
    status: str
    notes: Optional[str]
    metadata: Optional[Mapping[str, Any]]
    created_at: datetime


@dataclass(slots=True)
class RiskEventRecord:
    """Persisted record describing a triggered risk finding."""

    event_id: str
    user_id: str
    category: str
    severity: str
    message: str
    attributes: Mapping[str, Any]
    created_at: datetime


@dataclass(slots=True)
class KnownDeviceRecord:
    """Tracked device previously observed for a user."""

    user_id: str
    device_id: str
    first_seen: datetime
    last_seen: datetime


@dataclass(slots=True)
class OrganizationNodeRecord:
    """Represents a node in the organization tree."""

    node_id: str
    user_id: str
    tree_type: str  # "unilevel" or "binary"
    parent_node_id: Optional[str]
    sponsor_user_id: Optional[str]
    position: Optional[str]
    depth: int
    path: str
    created_at: datetime
    updated_at: datetime
    rank: Optional[str] = None
    center_id: Optional[str] = None


@dataclass(slots=True)
class SpilloverLogRecord:
    """Record of a spillover event for auditing."""

    log_id: str
    tree_type: str
    sponsor_user_id: str
    assigned_user_id: str
    parent_node_id: str
    position: str
    created_at: datetime


@dataclass(slots=True)
class BonusEntryRecord:
    """Bonus ledger entry created by the bonus distribution engine."""

    bonus_id: str
    user_id: str
    source_user_id: str
    bonus_type: str
    level: int
    status: str
    metadata: Mapping[str, Any]
    created_at: datetime
    order_id: Optional[str] = None
    pv_amount: Optional[Decimal] = None
    bonus_amount: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    hold_until: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        metadata_mapping: Mapping[str, Any] = self.metadata if isinstance(self.metadata, Mapping) else {}
        self.metadata = dict(metadata_mapping)

        if self.bonus_amount is None and self.amount is not None:
            self.bonus_amount = self.amount
        elif self.bonus_amount is not None and self.amount is None:
            self.amount = self.bonus_amount

        if self.bonus_amount is None:
            raise ValueError("bonus_amount must be provided via 'bonus_amount' or legacy 'amount'.")

        if self.order_id is None:
            order_id = self.metadata.get("order_id")
            if order_id is not None:
                self.order_id = str(order_id)

        if self.order_id is None:
            raise ValueError("order_id must be provided on bonus entries.")

        if self.pv_amount is None:
            pv_value = self.metadata.get("pv_amount")
            if pv_value is not None:
                self.pv_amount = Decimal(str(pv_value))

        if self.pv_amount is None:
            self.pv_amount = Decimal("0")


@dataclass(slots=True)
class BonusRetryRecord:
    """Queue record describing a bonus entry awaiting retry processing."""

    queue_id: str
    bonus_id: str
    order_id: str
    bonus_type: str
    failure_reason: Optional[str]
    retry_after: Optional[datetime]
    retry_count: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass(slots=True)
class OrganizationKpiRecord:
    """Daily KPI snapshot for an organization node."""

    node_id: str
    tree_type: str
    metric_date: date
    personal_volume: Decimal
    group_volume: Decimal
    volume_left: Optional[Decimal]
    volume_right: Optional[Decimal]
    orders_count: int


@dataclass(slots=True)
class OrderRecord:
    """Commerce order persisted for PV/bonus processing."""

    order_id: str
    user_id: str
    total_amount: Decimal
    pv_amount: Decimal
    status: str
    channel: str
    metadata: Mapping[str, Any]
    created_at: datetime


@dataclass(slots=True)
class IdempotencyKeyRecord:
    """Idempotency token used to protect inbound commerce requests."""

    key: str
    scope: str
    payload_hash: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    resource_id: Optional[str] = None


@dataclass(slots=True)
class ProductRecord:
    """Product catalog entry."""

    product_id: str
    name: str
    price: Decimal
    pv: Decimal
    status: str
    metadata: Mapping[str, Any]
    updated_at: datetime


@dataclass(slots=True)
class UserRecord:
    """User identity linked to OAuth providers."""

    user_id: str
    provider: str
    subject: str
    roles: tuple[str, ...]
    two_factor_enabled: bool = False


@dataclass(slots=True)
class UserAccountRecord:
    """Primary account information for locally registered users."""

    user_id: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime


@dataclass(slots=True)
class SessionRecord:
    """Authentication session information."""

    token: str
    user_id: str
    roles: tuple[str, ...]
    expires_at: float


@dataclass(slots=True)
class TwoFactorRecord:
    """Stored two-factor authentication secret."""

    user_id: str
    secret: str
    enabled: bool
    updated_at: float
    recovery_codes: tuple[str, ...] = ()


@dataclass(slots=True)
class LoginAuditRecord:
    """Audit log entry for authentication events."""

    provider: str
    status: str
    subject: Optional[str] = None
    reason: Optional[str] = None


class LoginAuditRepository(Protocol):
    """Persistence operations for authentication audit logging."""

    def log(self, record: LoginAuditRecord) -> None:
        ...

    def list_recent(self, *, limit: int = 100) -> Sequence[LoginAuditRecord]:
        ...


class UserRepository(Protocol):
    """Lookup operations for application users."""

    def find_by_oauth_identity(self, provider: str, subject: str) -> Optional[UserRecord]:
        ...

    def create_identity(self, record: UserRecord) -> None:
        ...


class UserAccountRepository(Protocol):
    """Persistence operations for locally registered user accounts."""

    def save(self, record: UserAccountRecord) -> None:
        ...

    def find_by_email(self, email: str) -> Optional[UserAccountRecord]:
        ...

    def find(self, user_id: str) -> Optional[UserAccountRecord]:
        ...


class SessionRepository(Protocol):
    """Persistence operations for authentication sessions."""

    def create_session(self, record: SessionRecord) -> SessionRecord:
        ...

    def get_session(self, token: str) -> Optional[SessionRecord]:
        ...


class TwoFactorRepository(Protocol):
    """Persistence operations for two-factor secrets."""

    def get(self, user_id: str) -> Optional[TwoFactorRecord]:
        ...

    def save(self, record: TwoFactorRecord) -> None:
        ...

    def disable(self, user_id: str) -> None:
        ...


class WalletRepository(Protocol):
    """Persistence operations required by WalletService."""

    def save_wallet(self, wallet: WalletRecord) -> None:
        ...

    def log_transaction(self, transaction: TransactionRecord) -> None:
        ...


class PointWalletRepository(Protocol):
    """Persistence operations for internal point wallets and withdrawals."""

    def get_wallet(self, wallet_id: str) -> Optional[PointWalletRecord]:
        ...

    def get_wallet_by_user(self, user_id: str) -> Optional[PointWalletRecord]:
        ...

    def create_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        ...

    def update_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        ...

    def add_ledger_entry(self, entry: PointLedgerRecord) -> None:
        ...

    def get_withdrawal_request(self, request_id: str) -> Optional[WithdrawalRequestRecord]:
        ...

    def create_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        ...

    def update_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        ...

    def list_withdrawal_requests(
        self,
        *,
        wallet_id: str,
        statuses: Sequence[str] | None = None,
    ) -> Sequence[WithdrawalRequestRecord]:
        ...


class WithdrawalAuditRepository(Protocol):
    """Persistence operations for withdrawal workflow audit logs."""

    def log(self, record: WithdrawalAuditRecord) -> None:
        ...

    def list_for_request(self, request_id: str, *, limit: int = 100) -> Sequence[WithdrawalAuditRecord]:
        ...


class RiskRepository(Protocol):
    """Persistence operations for risk detection signals."""

    def record_event(self, record: RiskEventRecord) -> None:
        ...

    def list_recent(self, user_id: str, *, limit: int = 50) -> Sequence[RiskEventRecord]:
        ...

    def get_known_device(self, user_id: str, device_id: str) -> Optional[KnownDeviceRecord]:
        ...

    def upsert_known_device(self, record: KnownDeviceRecord) -> None:
        ...


class OrganizationRepository(Protocol):
    """Persistence operations for organization trees and spillover logging."""

    def create_node(self, record: OrganizationNodeRecord) -> OrganizationNodeRecord:
        ...

    def get_node(self, node_id: str) -> Optional[OrganizationNodeRecord]:
        ...

    def get_node_by_user(self, tree_type: str, user_id: str) -> Optional[OrganizationNodeRecord]:
        ...

    def list_children(self, node_id: str) -> Sequence[OrganizationNodeRecord]:
        ...

    def log_spillover(self, record: SpilloverLogRecord) -> None:
        ...

    def list_spillovers(self, sponsor_user_id: str, *, limit: int = 100) -> Sequence[SpilloverLogRecord]:
        ...

    def get_nodes_by_ids(self, node_ids: Sequence[str]) -> Sequence[OrganizationNodeRecord]:
        ...

    def is_descendant(self, *, ancestor_node_id: str, descendant_node_id: str, tree_type: str) -> bool:
        ...


class OrganizationMetricsRepository(Protocol):
    """Persistence operations for organization KPI metrics."""

    def list_metrics(
        self,
        node_id: str,
        *,
        tree_type: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[OrganizationKpiRecord]:
        ...


class BonusRepository(Protocol):
    """Persistence operations for bonus entries."""

    def record_bonus(self, record: BonusEntryRecord) -> None:
        ...

    def list_pending(self, *, limit: int = 100) -> Sequence[BonusEntryRecord]:
        ...

    def get_entry(self, bonus_id: str) -> Optional[BonusEntryRecord]:
        ...

    def mark_confirmed(self, bonus_id: str) -> None:
        ...

    def schedule_retry(self, bonus_id: str, retry_after: datetime, metadata: Mapping[str, Any]) -> None:
        ...

    def mark_failed(self, bonus_id: str, metadata: Mapping[str, Any]) -> None:
        ...

    def list_retry_candidates(self, *, now: datetime, limit: int = 100) -> Sequence[BonusRetryRecord]:
        ...

    def mark_retry_started(self, queue_id: str, *, started_at: datetime) -> None:
        ...

    def mark_retry_completed(self, queue_id: str, *, completed_at: datetime) -> None:
        ...

    def mark_retry_failed(self, queue_id: str, *, failed_at: datetime, metadata: Mapping[str, Any]) -> None:
        ...


class OrderRepository(Protocol):
    """Persistence operations for commerce orders."""

    def get_order(self, order_id: str) -> Optional[OrderRecord]:
        ...

    def upsert_order(self, record: OrderRecord) -> OrderRecord:
        ...


class IdempotencyRepository(Protocol):
    """Persistence layer for idempotency key tracking."""

    def create(self, record: IdempotencyKeyRecord) -> bool:
        ...

    def get(self, *, key: str, scope: str) -> Optional[IdempotencyKeyRecord]:
        ...

    def mark_status(self, *, key: str, scope: str, status: str, resource_id: Optional[str] = None) -> None:
        ...


class ProductRepository(Protocol):
    """Product catalog access for commerce services."""

    def get_product(self, product_id: str) -> Optional[ProductRecord]:
        ...

    def list_products(self, *, status: Optional[str] = None) -> Sequence[ProductRecord]:
        ...


class MiningRepository(Protocol):
    """Persistence operations required by MiningService."""

    def upsert_balance(self, record: MiningBalanceRecord) -> None:
        ...

    def log_withdrawal(self, record: WithdrawalRecord) -> None:
        ...
