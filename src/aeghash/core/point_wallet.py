"""Domain logic for internal point wallets and withdrawal requests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import uuid
from typing import Callable, Mapping, MutableMapping, Optional, Sequence

from aeghash.core.repositories import (
    PointLedgerRecord,
    PointWalletRecord,
    PointWalletRepository,
    WithdrawalRequestRecord,
)


WALLET_STATUS_ACTIVE = "active"
WALLET_STATUS_SUSPENDED = "suspended"

LEDGER_TYPE_CREDIT = "credit"
LEDGER_TYPE_DEBIT = "debit"
LEDGER_TYPE_HOLD = "hold"
LEDGER_TYPE_RELEASE = "release"
LEDGER_TYPE_WITHDRAWAL = "withdrawal"

WITHDRAWAL_STATUS_PENDING = "pending"
WITHDRAWAL_STATUS_APPROVED = "approved"
WITHDRAWAL_STATUS_APPROVED_STAGE1 = "approved_pending"
WITHDRAWAL_STATUS_REJECTED = "rejected"
WITHDRAWAL_STATUS_CANCELLED = "cancelled"
WITHDRAWAL_STATUS_FAILED = "failed"


class PointWalletError(ValueError):
    """Base error for point wallet operations."""


class WalletNotFound(PointWalletError):
    """Raised when the requested wallet does not exist."""


class WalletSuspended(PointWalletError):
    """Raised when an operation is attempted on a suspended wallet."""


class InsufficientBalance(PointWalletError):
    """Raised when the wallet does not have enough available balance."""


class WithdrawalNotFound(PointWalletError):
    """Raised when a withdrawal request cannot be located."""


class InvalidWithdrawalState(PointWalletError):
    """Raised when a withdrawal request transition is not allowed."""


@dataclass(slots=True)
class PointWalletSnapshot:
    """Immutable snapshot of a wallet state returned by the service."""

    wallet_id: str
    user_id: str
    balance: Decimal
    pending_withdrawal: Decimal
    status: str

    @property
    def available_balance(self) -> Decimal:
        return self.balance - self.pending_withdrawal


@dataclass(slots=True)
class WithdrawalSnapshot:
    """Snapshot of a withdrawal request."""

    request_id: str
    wallet_id: str
    amount: Decimal
    status: str
    requested_by: str
    reference_id: Optional[str]
    created_at: datetime
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    notes: Optional[str]
    metadata: Optional[Mapping[str, object]] = None


class PointWalletService:
    """Service encapsulating point balance adjustments and withdrawal flow."""

    def __init__(
        self,
        repository: PointWalletRepository,
        *,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or (lambda: datetime.now(UTC))

    # ------------------------------------------------------------------ wallet

    def ensure_wallet(self, *, user_id: str) -> PointWalletSnapshot:
        record = self._repository.get_wallet_by_user(user_id)
        if record:
            return self._to_snapshot(record)

        now = self._now()
        record = PointWalletRecord(
            wallet_id=self._new_id(),
            user_id=user_id,
            balance=Decimal("0"),
            pending_withdrawal=Decimal("0"),
            status=WALLET_STATUS_ACTIVE,
            created_at=now,
            updated_at=now,
        )
        persisted = self._repository.create_wallet(record)
        return self._to_snapshot(persisted)

    def get_wallet(self, wallet_id: str) -> PointWalletSnapshot:
        record = self._repository.get_wallet(wallet_id)
        if not record:
            raise WalletNotFound(f"Wallet '{wallet_id}' was not found.")
        return self._to_snapshot(record)

    def get_wallet_by_user(self, user_id: str) -> PointWalletSnapshot:
        record = self._repository.get_wallet_by_user(user_id)
        if not record:
            raise WalletNotFound(f"Wallet for user '{user_id}' was not found.")
        return self._to_snapshot(record)

    def credit(
        self,
        *,
        user_id: str,
        amount: Decimal,
        reference_id: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> PointWalletSnapshot:
        wallet_record = self._get_or_create_record(user_id)
        self._assert_active(wallet_record)
        value = self._ensure_positive(amount)
        wallet_record.balance += value
        wallet_record.updated_at = self._now()
        updated = self._repository.update_wallet(wallet_record)
        self._append_ledger(
            updated,
            entry_type=LEDGER_TYPE_CREDIT,
            amount=value,
            reference_id=reference_id,
            metadata=metadata,
        )
        return self._to_snapshot(updated)

    def debit(
        self,
        *,
        wallet_id: str,
        amount: Decimal,
        reference_id: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> PointWalletSnapshot:
        wallet = self._require_wallet(wallet_id)
        self._assert_active(wallet)
        value = self._ensure_positive(amount)
        self._ensure_sufficient(wallet, value)
        wallet.balance -= value
        wallet.updated_at = self._now()
        updated = self._repository.update_wallet(wallet)
        self._append_ledger(
            updated,
            entry_type=LEDGER_TYPE_DEBIT,
            amount=value,
            reference_id=reference_id,
            metadata=metadata,
        )
        return self._to_snapshot(updated)

    # -------------------------------------------------------------- withdrawals

    def request_withdrawal(
        self,
        *,
        wallet_id: str,
        amount: Decimal,
        requested_by: str,
        reference_id: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> WithdrawalSnapshot:
        wallet = self._require_wallet(wallet_id, expected_user_id=requested_by)
        self._assert_active(wallet)
        value = self._ensure_positive(amount)
        self._ensure_sufficient(wallet, value)

        wallet.pending_withdrawal += value
        wallet.updated_at = self._now()
        updated_wallet = self._repository.update_wallet(wallet)

        request = WithdrawalRequestRecord(
            request_id=self._new_id(),
            wallet_id=wallet_id,
            amount=value,
            status=WITHDRAWAL_STATUS_PENDING,
            requested_by=requested_by,
            reference_id=reference_id,
            metadata=dict(metadata) if metadata is not None else None,
            created_at=self._now(),
        )
        persisted = self._repository.create_withdrawal_request(request)

        self._append_ledger(
            updated_wallet,
            entry_type=LEDGER_TYPE_HOLD,
            amount=value,
            reference_id=request.request_id,
            metadata={"reference_id": reference_id, "requested_by": requested_by},
        )
        return self._to_withdrawal_snapshot(persisted)

    def approve_withdrawal(
        self,
        request_id: str,
        *,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        if request.status not in {WITHDRAWAL_STATUS_PENDING, WITHDRAWAL_STATUS_APPROVED_STAGE1}:
            raise InvalidWithdrawalState(f"Withdrawal '{request_id}' is not pending.")

        wallet = self._require_wallet(request.wallet_id)
        self._assert_active(wallet)
        self._ensure_sufficient(wallet, request.amount, include_pending=True)

        wallet.balance -= request.amount
        wallet.pending_withdrawal -= request.amount
        wallet.updated_at = self._now()
        updated_wallet = self._repository.update_wallet(wallet)

        request = replace(
            request,
            status=WITHDRAWAL_STATUS_APPROVED,
            approved_by=approved_by,
            approved_at=self._now(),
            notes=notes,
        )
        persisted = self._repository.update_withdrawal_request(request)

        self._append_ledger(
            updated_wallet,
            entry_type=LEDGER_TYPE_WITHDRAWAL,
            amount=request.amount,
            reference_id=request.request_id,
            metadata={"approved_by": approved_by, "notes": notes},
        )
        return self._to_withdrawal_snapshot(persisted)

    def mark_stage1_approval(
        self,
        request_id: str,
        *,
        approver_id: str,
        notes: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        if request.status != WITHDRAWAL_STATUS_PENDING:
            raise InvalidWithdrawalState(f"Withdrawal '{request_id}' is not pending.")

        merged_metadata = dict(request.metadata or {})
        if metadata:
            merged_metadata.update(metadata)
        merged_metadata.setdefault("stage1_approver", approver_id)
        if notes:
            merged_metadata.setdefault("stage1_notes", notes)

        updated_request = replace(
            request,
            status=WITHDRAWAL_STATUS_APPROVED_STAGE1,
            metadata=merged_metadata,
        )
        persisted = self._repository.update_withdrawal_request(updated_request)
        return self._to_withdrawal_snapshot(persisted)

    def fail_withdrawal(
        self,
        request_id: str,
        *,
        failed_by: str,
        reason: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        if request.status not in {WITHDRAWAL_STATUS_APPROVED, WITHDRAWAL_STATUS_APPROVED_STAGE1}:
            raise InvalidWithdrawalState(f"Withdrawal '{request_id}' is not approved.")

        wallet = self._require_wallet(request.wallet_id)
        if request.status == WITHDRAWAL_STATUS_APPROVED:
            wallet.balance += request.amount
        wallet.pending_withdrawal = max(Decimal("0"), wallet.pending_withdrawal - request.amount)
        wallet.updated_at = self._now()
        updated_wallet = self._repository.update_wallet(wallet)

        request = replace(
            request,
            status=WITHDRAWAL_STATUS_FAILED,
            rejected_by=failed_by,
            rejected_at=self._now(),
            notes=reason,
        )
        persisted = self._repository.update_withdrawal_request(request)

        self._append_ledger(
            updated_wallet,
            entry_type=LEDGER_TYPE_RELEASE,
            amount=request.amount,
            reference_id=request.request_id,
            metadata={"failed_by": failed_by, "reason": reason},
        )
        return self._to_withdrawal_snapshot(persisted)


    def reject_withdrawal(
        self,
        request_id: str,
        *,
        rejected_by: str,
        notes: Optional[str] = None,
    ) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        if request.status != WITHDRAWAL_STATUS_PENDING:
            raise InvalidWithdrawalState(f"Withdrawal '{request_id}' is not pending.")

        wallet = self._require_wallet(request.wallet_id)
        self._ensure_pending_amount(wallet, request.amount)
        wallet.pending_withdrawal -= request.amount
        wallet.updated_at = self._now()
        updated_wallet = self._repository.update_wallet(wallet)

        request = replace(
            request,
            status=WITHDRAWAL_STATUS_REJECTED,
            rejected_by=rejected_by,
            rejected_at=self._now(),
            notes=notes,
        )
        persisted = self._repository.update_withdrawal_request(request)

        self._append_ledger(
            updated_wallet,
            entry_type=LEDGER_TYPE_RELEASE,
            amount=request.amount,
            reference_id=request.request_id,
            metadata={"rejected_by": rejected_by, "notes": notes},
        )
        return self._to_withdrawal_snapshot(persisted)

    def cancel_withdrawal(self, request_id: str, *, cancelled_by: str) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        if request.status != WITHDRAWAL_STATUS_PENDING:
            raise InvalidWithdrawalState(f"Withdrawal '{request_id}' is not pending.")

        wallet = self._require_wallet(request.wallet_id)
        self._ensure_pending_amount(wallet, request.amount)
        wallet.pending_withdrawal -= request.amount
        wallet.updated_at = self._now()
        updated_wallet = self._repository.update_wallet(wallet)

        request = replace(
            request,
            status=WITHDRAWAL_STATUS_CANCELLED,
            rejected_by=cancelled_by,
            rejected_at=self._now(),
        )
        persisted = self._repository.update_withdrawal_request(request)

        self._append_ledger(
            updated_wallet,
            entry_type=LEDGER_TYPE_RELEASE,
            amount=request.amount,
            reference_id=request.request_id,
            metadata={"cancelled_by": cancelled_by},
        )
        return self._to_withdrawal_snapshot(persisted)

    def annotate_withdrawal(self, request_id: str, metadata: Mapping[str, object]) -> WithdrawalSnapshot:
        request = self._require_withdrawal(request_id)
        merged = dict(request.metadata or {})
        merged.update(metadata)
        updated_request = replace(request, metadata=merged)
        persisted = self._repository.update_withdrawal_request(updated_request)
        return self._to_withdrawal_snapshot(persisted)

    def get_withdrawal(self, request_id: str) -> WithdrawalSnapshot:
        record = self._repository.get_withdrawal_request(request_id)
        if not record:
            raise WithdrawalNotFound(f"Withdrawal '{request_id}' was not found.")
        return self._to_withdrawal_snapshot(record)

    def list_withdrawals(
        self,
        *,
        wallet_id: str,
        statuses: Sequence[str] | None = None,
    ) -> list[WithdrawalSnapshot]:
        records = self._repository.list_withdrawal_requests(wallet_id=wallet_id, statuses=statuses)
        return [self._to_withdrawal_snapshot(record) for record in records]

    # ----------------------------------------------------------------- helpers

    def _get_or_create_record(self, user_id: str) -> PointWalletRecord:
        record = self._repository.get_wallet_by_user(user_id)
        if record:
            return record
        now = self._now()
        record = PointWalletRecord(
            wallet_id=self._new_id(),
            user_id=user_id,
            balance=Decimal("0"),
            pending_withdrawal=Decimal("0"),
            status=WALLET_STATUS_ACTIVE,
            created_at=now,
            updated_at=now,
        )
        return self._repository.create_wallet(record)

    def _require_wallet(self, wallet_id: str, *, expected_user_id: Optional[str] = None) -> PointWalletRecord:
        record = self._repository.get_wallet(wallet_id)
        if not record:
            raise WalletNotFound(f"Wallet '{wallet_id}' was not found.")
        if expected_user_id and record.user_id != expected_user_id:
            raise WalletNotFound(f"Wallet '{wallet_id}' was not found.")
        return record

    def _require_withdrawal(self, request_id: str) -> WithdrawalRequestRecord:
        record = self._repository.get_withdrawal_request(request_id)
        if not record:
            raise WithdrawalNotFound(f"Withdrawal request '{request_id}' was not found.")
        return record

    def _assert_active(self, wallet: PointWalletRecord) -> None:
        if wallet.status != WALLET_STATUS_ACTIVE:
            raise WalletSuspended(f"Wallet '{wallet.wallet_id}' is suspended.")

    def _ensure_positive(self, amount: Decimal) -> Decimal:
        value = self._to_decimal(amount)
        if value <= 0:
            raise PointWalletError("Amount must be positive.")
        return value

    def _ensure_sufficient(self, wallet: PointWalletRecord, amount: Decimal, *, include_pending: bool = False) -> None:
        available = wallet.balance - wallet.pending_withdrawal
        if include_pending:
            available = wallet.balance
        if amount > available:
            raise InsufficientBalance("Insufficient wallet balance.")

    def _ensure_pending_amount(self, wallet: PointWalletRecord, amount: Decimal) -> None:
        if wallet.pending_withdrawal < amount:
            raise PointWalletError("Pending withdrawal amount is insufficient to release.")

    def _append_ledger(
        self,
        wallet: PointWalletRecord,
        *,
        entry_type: str,
        amount: Decimal,
        reference_id: Optional[str],
        metadata: Optional[Mapping[str, object]],
    ) -> None:
        payload: Optional[MutableMapping[str, object]]
        if metadata is None:
            payload = None
        else:
            payload = dict(metadata)
        entry = PointLedgerRecord(
            entry_id=self._new_id(),
            wallet_id=wallet.wallet_id,
            entry_type=entry_type,
            amount=amount,
            balance_after=wallet.balance,
            pending_after=wallet.pending_withdrawal,
            reference_id=reference_id,
            metadata=payload,
            created_at=self._now(),
        )
        self._repository.add_ledger_entry(entry)

    def _to_snapshot(self, record: PointWalletRecord) -> PointWalletSnapshot:
        return PointWalletSnapshot(
            wallet_id=record.wallet_id,
            user_id=record.user_id,
            balance=record.balance,
            pending_withdrawal=record.pending_withdrawal,
            status=record.status,
        )

    def _to_withdrawal_snapshot(self, record: WithdrawalRequestRecord) -> WithdrawalSnapshot:
        return WithdrawalSnapshot(
            request_id=record.request_id,
            wallet_id=record.wallet_id,
            amount=record.amount,
            status=record.status,
            requested_by=record.requested_by,
            reference_id=record.reference_id,
            created_at=record.created_at,
            approved_by=record.approved_by,
            approved_at=record.approved_at,
            rejected_by=record.rejected_by,
            rejected_at=record.rejected_at,
            notes=record.notes,
            metadata=record.metadata,
        )

    def _new_id(self) -> str:
        return self._id_factory()

    def _now(self) -> datetime:
        return self._clock()

    @staticmethod
    def _to_decimal(value: Decimal | int | str) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, int):
            return Decimal(value)
        return Decimal(str(value))
