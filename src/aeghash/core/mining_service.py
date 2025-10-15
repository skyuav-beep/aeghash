"""Mining service orchestrating HashDam client operations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aeghash.adapters.hashdam import AssetWithdrawal, HashBalance, HashDamClient
from aeghash.core.repositories import MiningBalanceRecord, MiningRepository, WithdrawalRecord
from aeghash.utils import NotificationMessage, Notifier, RetryConfig, retry


@dataclass(slots=True)
class WithdrawalRequest:
    """Represents a mining withdrawal request outcome."""

    withdraw_id: str
    coin: str
    amount: Decimal


class MiningService:
    """High-level orchestration for mining-related operations."""

    def __init__(
        self,
        client: HashDamClient,
        repository: MiningRepository,
        notifier: Notifier | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._client = client
        self._repository = repository
        self._notifier = notifier
        self._retry_config = retry_config or RetryConfig()

    def _notify_failure(self, message: str) -> None:
        if self._notifier:
            self._notifier.send(
                NotificationMessage(subject="Mining operation failure", body=message),
            )

    def get_balance(self, *, user_id: str) -> HashBalance:
        """Fetch current hash balance summary."""
        balance = self._client.get_hash_balance()
        self._repository.upsert_balance(MiningBalanceRecord(user_id=user_id, balance=balance))
        return balance

    def request_withdrawal(self, *, user_id: str, coin: str, amount: Decimal) -> WithdrawalRequest:
        """Request mining asset withdrawal."""
        @retry(self._retry_config, on_failure=lambda exc, attempt: self._notify_failure(f"Withdrawal attempt {attempt} failed: {exc}"))
        def _withdraw() -> AssetWithdrawal:
            return self._client.request_asset_withdrawal(coin=coin, amount=amount)

        try:
            result = _withdraw()
        except Exception:
            self._repository.log_withdrawal(
                WithdrawalRecord(
                    user_id=user_id,
                    withdraw_id=None,
                    coin=coin,
                    amount=amount,
                    status="failed",
                ),
            )
            raise
        self._repository.log_withdrawal(
            WithdrawalRecord(
                user_id=user_id,
                withdraw_id=result.withdraw_id,
                coin=result.coin,
                amount=result.amount,
                status="submitted",
            ),
        )
        return WithdrawalRequest(
            withdraw_id=result.withdraw_id,
            coin=result.coin,
            amount=result.amount,
        )
