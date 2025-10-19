from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Optional, Sequence

import pytest

from aeghash.core.point_wallet import (
    InsufficientBalance,
    InvalidWithdrawalState,
    PointWalletService,
    WALLET_STATUS_SUSPENDED,
    WithdrawalNotFound,
    WalletNotFound,
    WalletSuspended,
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_CANCELLED,
    WITHDRAWAL_STATUS_PENDING,
    WITHDRAWAL_STATUS_REJECTED,
    WalletNotFound,
)
from aeghash.core.repositories import (
    PointLedgerRecord,
    PointWalletRecord,
    PointWalletRepository,
    WithdrawalRequestRecord,
)


class InMemoryPointWalletRepository(PointWalletRepository):
    def __init__(self) -> None:
        self.wallets: dict[str, PointWalletRecord] = {}
        self.wallets_by_user: dict[str, str] = {}
        self.ledger: list[PointLedgerRecord] = []
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
        records: list[WithdrawalRequestRecord] = []
        for request in self.withdrawals.values():
            if request.wallet_id != wallet_id:
                continue
            if statuses and request.status not in statuses:
                continue
            records.append(request)
        return sorted(records, key=lambda item: item.created_at)


def fixed_clock():
    return datetime(2025, 5, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def repository() -> InMemoryPointWalletRepository:
    return InMemoryPointWalletRepository()


@pytest.fixture()
def service(repository: InMemoryPointWalletRepository) -> PointWalletService:
    counter = 0

    def id_factory() -> str:
        nonlocal counter
        counter += 1
        return f"id-{counter}"

    return PointWalletService(repository, id_factory=id_factory, clock=fixed_clock)


def test_ensure_wallet_creates_new_record(service: PointWalletService, repository: InMemoryPointWalletRepository):
    snapshot = service.ensure_wallet(user_id="user-1")

    assert snapshot.user_id == "user-1"
    assert snapshot.balance == Decimal("0")
    assert snapshot.pending_withdrawal == Decimal("0")
    assert repository.get_wallet(snapshot.wallet_id) is not None


def test_credit_increments_balance_and_creates_ledger(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("100"))

    assert wallet.balance == Decimal("100")
    assert wallet.available_balance == Decimal("100")
    assert repository.ledger[-1].entry_type == "credit"
    assert repository.ledger[-1].balance_after == Decimal("100")


def test_debit_requires_sufficient_balance(service: PointWalletService):
    service.credit(user_id="user-1", amount=Decimal("50"))
    with pytest.raises(InsufficientBalance):
        service.debit(wallet_id=service.get_wallet_by_user("user-1").wallet_id, amount=Decimal("70"))


def test_debit_reduces_balance(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("80"))
    updated = service.debit(wallet_id=wallet.wallet_id, amount=Decimal("30"), reference_id="order-1")

    assert updated.balance == Decimal("50")
    assert repository.ledger[-1].entry_type == "debit"
    assert repository.ledger[-1].reference_id == "order-1"


def test_request_withdrawal_moves_amount_to_pending(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("120"))
    withdrawal = service.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("70"),
        requested_by="user-1",
        reference_id="req-1",
    )

    updated_wallet = service.get_wallet(wallet.wallet_id)
    assert updated_wallet.balance == Decimal("120")
    assert updated_wallet.pending_withdrawal == Decimal("70")
    assert updated_wallet.available_balance == Decimal("50")
    assert withdrawal.status == WITHDRAWAL_STATUS_PENDING
    assert repository.ledger[-1].entry_type == "hold"


def test_request_withdrawal_enforces_wallet_owner(service: PointWalletService):
    wallet = service.credit(user_id="user-1", amount=Decimal("50"))
    with pytest.raises(WalletNotFound):
        service.request_withdrawal(
            wallet_id=wallet.wallet_id,
            amount=Decimal("10"),
            requested_by="user-2",
        )


def test_approve_withdrawal_deducts_balance(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("150"))
    withdrawal = service.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("40"),
        requested_by="user-1",
    )

    result = service.approve_withdrawal(withdrawal.request_id, approved_by="admin-1", notes="approved")

    assert result.status == WITHDRAWAL_STATUS_APPROVED
    updated_wallet = service.get_wallet(wallet.wallet_id)
    assert updated_wallet.balance == Decimal("110")
    assert updated_wallet.pending_withdrawal == Decimal("0")
    assert repository.ledger[-1].entry_type == "withdrawal"


def test_reject_withdrawal_releases_pending_amount(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("60"))
    withdrawal = service.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("30"),
        requested_by="user-1",
    )

    result = service.reject_withdrawal(withdrawal.request_id, rejected_by="admin-1", notes="kyc failure")

    assert result.status == WITHDRAWAL_STATUS_REJECTED
    updated_wallet = service.get_wallet(wallet.wallet_id)
    assert updated_wallet.balance == Decimal("60")
    assert updated_wallet.pending_withdrawal == Decimal("0")


def test_cancel_withdrawal(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.credit(user_id="user-1", amount=Decimal("90"))
    withdrawal = service.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("20"),
        requested_by="user-1",
    )

    result = service.cancel_withdrawal(withdrawal.request_id, cancelled_by="user-1")

    assert result.status == WITHDRAWAL_STATUS_CANCELLED
    updated_wallet = service.get_wallet(wallet.wallet_id)
    assert updated_wallet.pending_withdrawal == Decimal("0")


def test_rejecting_non_pending_withdrawal_raises(service: PointWalletService):
    wallet = service.credit(user_id="user-1", amount=Decimal("40"))
    withdrawal = service.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("10"),
        requested_by="user-1",
    )
    service.approve_withdrawal(withdrawal.request_id, approved_by="admin-1")

    with pytest.raises(InvalidWithdrawalState):
        service.reject_withdrawal(withdrawal.request_id, rejected_by="admin-2")


def test_withdrawal_not_found_raises(service: PointWalletService):
    with pytest.raises(WithdrawalNotFound):
        service.approve_withdrawal("missing", approved_by="admin")


def test_wallet_suspended_operations_blocked(service: PointWalletService, repository: InMemoryPointWalletRepository):
    wallet = service.ensure_wallet(user_id="user-1")
    record = repository.get_wallet(wallet.wallet_id)
    assert record is not None
    record.status = WALLET_STATUS_SUSPENDED
    repository.update_wallet(record)

    with pytest.raises(WalletSuspended):
        service.credit(user_id="user-1", amount=Decimal("10"))


def test_wallet_not_found(service: PointWalletService):
    with pytest.raises(WalletNotFound):
        service.get_wallet("unknown")
