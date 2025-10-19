"""Workflows bridging platform withdrawals with HashDam mining service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from aeghash.core.mining_service import MiningService, WithdrawalRequest as MiningWithdrawalRequest
from aeghash.core.point_wallet import (
    PointWalletService,
    WithdrawalSnapshot,
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_APPROVED_STAGE1,
)
from aeghash.utils import NotificationMessage, Notifier


class WithdrawalExecutionError(RuntimeError):
    """Raised when HashDam withdrawal execution fails after local approval."""


@dataclass(slots=True)
class WithdrawalExecutionOutcome:
    """Result payload returned when orchestrating a withdrawal."""

    withdrawal: WithdrawalSnapshot
    mining_request: MiningWithdrawalRequest


class MiningWithdrawalOrchestrator:
    """Coordinates platform withdrawal approval with HashDam execution."""

    def __init__(
        self,
        mining_service: MiningService,
        wallet_service: PointWalletService,
        notifier: Notifier | None = None,
    ) -> None:
        self._mining = mining_service
        self._wallets = wallet_service
        self._notifier = notifier

    def approve_and_execute(
        self,
        request_id: str,
        *,
        approved_by: str,
        notes: Optional[str] = None,
        coin: Optional[str] = None,
    ) -> WithdrawalExecutionOutcome:
        """Approve the platform withdrawal and trigger the HashDam transfer."""
        pending = self._wallets.get_withdrawal(request_id)
        if pending.status not in {"pending", WITHDRAWAL_STATUS_APPROVED_STAGE1, WITHDRAWAL_STATUS_APPROVED}:
            raise WithdrawalExecutionError(f"Withdrawal '{request_id}' is not eligible for execution.")

        wallet = self._wallets.get_wallet(pending.wallet_id)
        coin_symbol = coin or (pending.metadata or {}).get("coin")
        if not coin_symbol:
            raise WithdrawalExecutionError("Withdrawal metadata missing 'coin' value.")

        if pending.status == WITHDRAWAL_STATUS_APPROVED:
            approved = pending
        else:
            approved = self._wallets.approve_withdrawal(request_id, approved_by=approved_by, notes=notes)

        try:
            mining_result = self._mining.request_withdrawal(
                user_id=wallet.user_id,
                coin=str(coin_symbol),
                amount=pending.amount,
            )
        except Exception as exc:  # pragma: no cover - network/HashDam failure
            self._wallets.fail_withdrawal(request_id, failed_by=approved_by, reason=str(exc))
            if self._notifier:
                self._notifier.send(
                    NotificationMessage(
                        subject="HashDam withdrawal failure",
                        body=f"Request {request_id} for user {wallet.user_id} failed: {exc}",
                    ),
                )
            raise WithdrawalExecutionError(str(exc)) from exc

        return WithdrawalExecutionOutcome(withdrawal=approved, mining_request=mining_result)
