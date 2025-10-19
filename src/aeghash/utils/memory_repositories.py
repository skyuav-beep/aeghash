"""In-memory repository implementations for testing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, List, Mapping, Optional, Sequence

from aeghash.adapters.hashdam import HashBalance
from aeghash.core.repositories import (
    MiningBalanceRecord,
    MiningRepository,
    PointLedgerRecord,
    PointWalletRecord,
    PointWalletRepository,
    KnownDeviceRecord,
    RiskEventRecord,
    RiskRepository,
    OrganizationNodeRecord,
    OrganizationRepository,
    SpilloverLogRecord,
    BonusEntryRecord,
    BonusRepository,
    BonusRetryRecord,
    OrderRecord,
    OrderRepository,
    IdempotencyKeyRecord,
    IdempotencyRepository,
    ProductRecord,
    ProductRepository,
    TransactionRecord,
    WalletRecord,
    WalletRepository,
    WithdrawalRecord,
    WithdrawalRequestRecord,
    WithdrawalAuditRecord,
    WithdrawalAuditRepository,
)


@dataclass
class StoredWallet:
    record: WalletRecord


class InMemoryWalletRepository(WalletRepository):
    def __init__(self) -> None:
        self.wallets: List[WalletRecord] = []
        self.transactions: List[TransactionRecord] = []

    def save_wallet(self, wallet: WalletRecord) -> None:
        self.wallets.append(wallet)

    def log_transaction(self, transaction: TransactionRecord) -> None:
        self.transactions.append(transaction)


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self.orders: dict[str, OrderRecord] = {}

    def get_order(self, order_id: str) -> Optional[OrderRecord]:
        return self.orders.get(order_id)

    def upsert_order(self, record: OrderRecord) -> OrderRecord:
        self.orders[record.order_id] = record
        return record


class InMemoryIdempotencyRepository(IdempotencyRepository):
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], IdempotencyKeyRecord] = {}

    def create(self, record: IdempotencyKeyRecord) -> bool:
        key = (record.scope, record.key)
        if key in self.records:
            return False
        self.records[key] = record
        return True

    def get(self, *, key: str, scope: str) -> Optional[IdempotencyKeyRecord]:
        return self.records.get((scope, key))

    def mark_status(self, *, key: str, scope: str, status: str, resource_id: Optional[str] = None) -> None:
        record = self.records.get((scope, key))
        if not record:
            return
        record.status = status
        if resource_id is not None:
            record.resource_id = resource_id


class InMemoryProductRepository(ProductRepository):
    def __init__(self) -> None:
        self.products: dict[str, ProductRecord] = {}

    def get_product(self, product_id: str) -> Optional[ProductRecord]:
        return self.products.get(product_id)

    def list_products(self, *, status: Optional[str] = None) -> Sequence[ProductRecord]:
        values = list(self.products.values())
        if status:
            values = [product for product in values if product.status == status]
        return values


@dataclass
class StoredMiningBalance:
    user_id: str
    balance: HashBalance


class InMemoryMiningRepository(MiningRepository):
    def __init__(self) -> None:
        self.balances: List[MiningBalanceRecord] = []
        self.withdrawals: List[WithdrawalRecord] = []

    def upsert_balance(self, record: MiningBalanceRecord) -> None:
        self.balances.append(record)

    def log_withdrawal(self, record: WithdrawalRecord) -> None:
        self.withdrawals.append(record)


class InMemoryPointWalletRepository(PointWalletRepository):
    def __init__(self) -> None:
        self.wallets: dict[str, PointWalletRecord] = {}
        self.wallets_by_user: dict[str, str] = {}
        self.ledger: List[PointLedgerRecord] = []
        self.withdrawals: dict[str, WithdrawalRequestRecord] = {}

    def get_wallet(self, wallet_id: str) -> Optional[PointWalletRecord]:
        return self.wallets.get(wallet_id)

    def get_wallet_by_user(self, user_id: str) -> Optional[PointWalletRecord]:
        wallet_id = self.wallets_by_user.get(user_id)
        if not wallet_id:
            return None
        return self.wallets.get(wallet_id)

    def create_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        self.wallets[record.wallet_id] = record
        self.wallets_by_user[record.user_id] = record.wallet_id
        return record

    def update_wallet(self, record: PointWalletRecord) -> PointWalletRecord:
        self.wallets[record.wallet_id] = record
        return record

    def add_ledger_entry(self, entry: PointLedgerRecord) -> None:
        self.ledger.append(entry)

    def get_withdrawal_request(self, request_id: str) -> Optional[WithdrawalRequestRecord]:
        return self.withdrawals.get(request_id)

    def create_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        self.withdrawals[record.request_id] = record
        return record

    def update_withdrawal_request(self, record: WithdrawalRequestRecord) -> WithdrawalRequestRecord:
        self.withdrawals[record.request_id] = record
        return record

    def list_withdrawal_requests(
        self,
        *,
        wallet_id: str,
        statuses: Sequence[str] | None = None,
    ) -> Sequence[WithdrawalRequestRecord]:
        records = [
            record
            for record in self.withdrawals.values()
            if record.wallet_id == wallet_id and (not statuses or record.status in statuses)
        ]
        return sorted(records, key=lambda item: item.created_at)


class InMemoryWithdrawalAuditRepository(WithdrawalAuditRepository):
    def __init__(self) -> None:
        self.records: list[WithdrawalAuditRecord] = []

    def log(self, record: WithdrawalAuditRecord) -> None:
        self.records.append(record)

    def list_for_request(self, request_id: str, *, limit: int = 100) -> Sequence[WithdrawalAuditRecord]:
        matching = [record for record in self.records if record.request_id == request_id]
        return sorted(matching, key=lambda item: item.created_at)[:limit]


class InMemoryRiskRepository(RiskRepository):
    def __init__(self) -> None:
        self.events: list[RiskEventRecord] = []
        self.devices: dict[tuple[str, str], KnownDeviceRecord] = {}

    def record_event(self, record: RiskEventRecord) -> None:
        self.events.append(record)

    def list_recent(self, user_id: str, *, limit: int = 50) -> Sequence[RiskEventRecord]:
        matching = [event for event in self.events if event.user_id == user_id]
        return sorted(matching, key=lambda event: event.created_at, reverse=True)[:limit]

    def get_known_device(self, user_id: str, device_id: str) -> Optional[KnownDeviceRecord]:
        return self.devices.get((user_id, device_id))

    def upsert_known_device(self, record: KnownDeviceRecord) -> None:
        self.devices[(record.user_id, record.device_id)] = record


class InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self) -> None:
        self.nodes: dict[str, OrganizationNodeRecord] = {}
        self.nodes_by_user: dict[tuple[str, str], str] = {}
        self.children: dict[str, list[OrganizationNodeRecord]] = {}
        self.spillovers: list[SpilloverLogRecord] = []

    def create_node(self, record: OrganizationNodeRecord) -> OrganizationNodeRecord:
        self.nodes[record.node_id] = record
        self.nodes_by_user[(record.tree_type, record.user_id)] = record.node_id
        if record.parent_node_id:
            self.children.setdefault(record.parent_node_id, []).append(record)
        else:
            self.children.setdefault(record.node_id, [])
        return record

    def get_node(self, node_id: str) -> Optional[OrganizationNodeRecord]:
        return self.nodes.get(node_id)

    def get_node_by_user(self, tree_type: str, user_id: str) -> Optional[OrganizationNodeRecord]:
        node_id = self.nodes_by_user.get((tree_type, user_id))
        return self.nodes.get(node_id) if node_id else None

    def list_children(self, node_id: str) -> Sequence[OrganizationNodeRecord]:
        return list(self.children.get(node_id, []))

    def log_spillover(self, record: SpilloverLogRecord) -> None:
        self.spillovers.append(record)

    def list_spillovers(self, sponsor_user_id: str, *, limit: int = 100) -> Sequence[SpilloverLogRecord]:
        matching = [record for record in self.spillovers if record.sponsor_user_id == sponsor_user_id]
        return matching[:limit]

    def get_nodes_by_ids(self, node_ids: Sequence[str]) -> Sequence[OrganizationNodeRecord]:
        return [self.nodes[node_id] for node_id in node_ids if node_id in self.nodes]


class InMemoryBonusRepository(BonusRepository):
    def __init__(self) -> None:
        self.records: dict[str, BonusEntryRecord] = {}
        self.retry_queue: dict[str, BonusRetryRecord] = {}

    def record_bonus(self, record: BonusEntryRecord) -> None:
        self.records[record.bonus_id] = record

    def list_pending(self, *, limit: int = 100) -> Sequence[BonusEntryRecord]:
        pending = [
            record for record in self.records.values() if record.status.upper() == "PENDING"
        ]
        pending.sort(key=lambda entry: entry.created_at)
        return pending[:limit]

    def get_entry(self, bonus_id: str) -> Optional[BonusEntryRecord]:
        return self.records.get(bonus_id)

    def mark_confirmed(self, bonus_id: str) -> None:
        record = self.records.get(bonus_id)
        if not record:
            return
        record.status = "CONFIRMED"
        record.confirmed_at = datetime.now(UTC)
        queue_id = f"retry-{bonus_id}"
        queue_record = self.retry_queue.get(queue_id)
        if queue_record:
            self.retry_queue[queue_id] = BonusRetryRecord(
                queue_id=queue_record.queue_id,
                bonus_id=queue_record.bonus_id,
                order_id=queue_record.order_id,
                bonus_type=queue_record.bonus_type,
                failure_reason=queue_record.failure_reason,
                retry_after=queue_record.retry_after,
                retry_count=queue_record.retry_count,
                status="COMPLETED",
                created_at=queue_record.created_at,
                updated_at=datetime.now(UTC),
            )

    def schedule_retry(self, bonus_id: str, retry_after: datetime, metadata: Mapping[str, Any]) -> None:
        record = self.records.get(bonus_id)
        if not record:
            return
        record.status = "RETRY"
        record.metadata = dict(metadata)
        record.hold_until = retry_after

        queue_id = f"retry-{bonus_id}"
        existing = self.retry_queue.get(queue_id)
        now = datetime.now(UTC)
        retry_count = int(metadata.get("retry_count", 0))
        failure_reason = (
            metadata.get("last_error") or metadata.get("reason") or metadata.get("failure_reason")
        )
        created_at = existing.created_at if existing else now
        self.retry_queue[queue_id] = BonusRetryRecord(
            queue_id=queue_id,
            bonus_id=bonus_id,
            order_id=record.order_id,
            bonus_type=record.bonus_type,
            failure_reason=str(failure_reason) if failure_reason else None,
            retry_after=retry_after,
            retry_count=retry_count if retry_count else (existing.retry_count if existing else 0),
            status="PENDING",
            created_at=created_at,
            updated_at=now,
        )

    def mark_failed(self, bonus_id: str, metadata: Mapping[str, Any]) -> None:
        record = self.records.get(bonus_id)
        if not record:
            return
        record.status = "FAILED"
        record.metadata = dict(metadata)
        queue_id = f"retry-{bonus_id}"
        queue_record = self.retry_queue.get(queue_id)
        if queue_record:
            now = datetime.now(UTC)
            failure_reason = (
                metadata.get("last_error") or metadata.get("reason") or metadata.get("failure_reason")
            )
            self.retry_queue[queue_id] = BonusRetryRecord(
                queue_id=queue_record.queue_id,
                bonus_id=queue_record.bonus_id,
                order_id=queue_record.order_id,
                bonus_type=queue_record.bonus_type,
                failure_reason=str(failure_reason) if failure_reason else queue_record.failure_reason,
                retry_after=queue_record.retry_after,
                retry_count=queue_record.retry_count,
                status="FAILED",
                created_at=queue_record.created_at,
                updated_at=now,
            )

    def list_retry_candidates(self, *, now: datetime, limit: int = 100) -> Sequence[BonusRetryRecord]:
        candidates = [
            record
            for record in self.retry_queue.values()
            if record.status == "PENDING" and (record.retry_after is None or record.retry_after <= now)
        ]
        candidates.sort(key=lambda entry: entry.retry_after or now)
        return candidates[:limit]

    def mark_retry_started(self, queue_id: str, *, started_at: datetime) -> None:
        record = self.retry_queue.get(queue_id)
        if not record:
            return
        self.retry_queue[queue_id] = BonusRetryRecord(
            queue_id=record.queue_id,
            bonus_id=record.bonus_id,
            order_id=record.order_id,
            bonus_type=record.bonus_type,
            failure_reason=record.failure_reason,
            retry_after=record.retry_after,
            retry_count=record.retry_count,
            status="PROCESSING",
            created_at=record.created_at,
            updated_at=started_at,
        )

    def mark_retry_completed(self, queue_id: str, *, completed_at: datetime) -> None:
        record = self.retry_queue.get(queue_id)
        if not record:
            return
        self.retry_queue[queue_id] = BonusRetryRecord(
            queue_id=record.queue_id,
            bonus_id=record.bonus_id,
            order_id=record.order_id,
            bonus_type=record.bonus_type,
            failure_reason=record.failure_reason,
            retry_after=record.retry_after,
            retry_count=record.retry_count,
            status="COMPLETED",
            created_at=record.created_at,
            updated_at=completed_at,
        )

    def mark_retry_failed(self, queue_id: str, *, failed_at: datetime, metadata: Mapping[str, Any]) -> None:
        record = self.retry_queue.get(queue_id)
        if not record:
            return
        failure_reason = (
            metadata.get("last_error") or metadata.get("reason") or metadata.get("failure_reason")
        )
        self.retry_queue[queue_id] = BonusRetryRecord(
            queue_id=record.queue_id,
            bonus_id=record.bonus_id,
            order_id=record.order_id,
            bonus_type=record.bonus_type,
            failure_reason=str(failure_reason) if failure_reason else record.failure_reason,
            retry_after=record.retry_after,
            retry_count=record.retry_count,
            status="FAILED",
            created_at=record.created_at,
            updated_at=failed_at,
        )
