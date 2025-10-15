"""Wallet service orchestrating MBlock client operations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from aeghash.adapters.mblock import MBlockClient, TransitToken, TransferReceipt, WalletInfo
from aeghash.config import MBlockSettings
from aeghash.core.repositories import TransactionRecord, WalletRecord, WalletRepository
from aeghash.utils import NotificationMessage, Notifier, RetryConfig, retry


@dataclass
class WalletServiceConfig:
    """Configuration derived from environment settings."""

    transit_fee: Optional[float]
    transit_fee_wallet_key: Optional[str]
    transit_callback_url: Optional[str]

    @classmethod
    def from_settings(cls, settings: MBlockSettings) -> "WalletServiceConfig":
        return cls(
            transit_fee=settings.transit_fee,
            transit_fee_wallet_key=settings.transit_fee_wallet_key,
            transit_callback_url=settings.transit_callback_url,
        )

    def build_transit_config(self) -> Optional[dict[str, object]]:
        """Build default transit config payload if values exist."""
        config: dict[str, object] = {}
        if self.transit_fee is not None:
            config["fee"] = self.transit_fee
        if self.transit_fee_wallet_key:
            config["feeWalletKey"] = self.transit_fee_wallet_key
        if self.transit_callback_url:
            config["callback"] = self.transit_callback_url
        return config or None


class WalletService:
    """High-level wallet orchestration around the MBlock API."""

    def __init__(
        self,
        client: MBlockClient,
        settings: MBlockSettings,
        repository: WalletRepository,
        notifier: Notifier | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._client = client
        self._config = WalletServiceConfig.from_settings(settings)
        self._repository = repository
        self._notifier = notifier
        self._retry_config = retry_config or RetryConfig()

    def _notify_failure(self, message: str) -> None:
        if self._notifier:
            self._notifier.send(
                NotificationMessage(subject="Wallet operation failure", body=message),
            )

    def create_wallet(self, *, user_id: str) -> WalletInfo:
        wallet = self._client.request_wallet()
        self._repository.save_wallet(
            WalletRecord(user_id=user_id, address=wallet.address, wallet_key=wallet.wallet_key),
        )
        return wallet

    def get_balance(self, *, address: str, contract: Optional[str] = None) -> Decimal:
        return self._client.get_balance(address=address, contract=contract)

    def transfer_token(
        self,
        *,
        wallet_id: str,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: Optional[str] = None,
        coin: Optional[str] = None,
    ) -> TransferReceipt:
        @retry(
            self._retry_config,
            on_failure=lambda exc, attempt: self._notify_failure(
                f"Transfer attempt {attempt} failed: {exc}",
            ),
        )
        def _transfer() -> TransferReceipt:
            return self._client.transfer_by_wallet_key(
                wallet_key=wallet_key,
                to=to,
                amount=amount,
                contract=contract,
            )

        try:
            receipt = _transfer()
        except Exception:
            self._repository.log_transaction(
                TransactionRecord(
                    wallet_id=wallet_id,
                    txid=None,
                    amount=amount,
                    coin=coin,
                    status="failed",
                ),
            )
            raise
        self._repository.log_transaction(
            TransactionRecord(
                wallet_id=wallet_id,
                txid=receipt.txid,
                amount=amount,
                coin=coin,
                status="submitted",
            ),
        )
        return receipt

    def request_transit(
        self,
        *,
        wallet_id: str,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: str,
        override_config: Optional[dict[str, object]] = None,
    ) -> TransitToken:
        base_config = self._config.build_transit_config()
        config: Optional[dict[str, object]]
        if base_config and override_config:
            merged: dict[str, object] = {**base_config, **override_config}
            config = merged
        else:
            config = override_config or base_config

        @retry(
            self._retry_config,
            on_failure=lambda exc, attempt: self._notify_failure(
                f"Transit attempt {attempt} failed: {exc}",
            ),
        )
        def _transit() -> TransitToken:
            return self._client.transit_by_wallet_key(
                wallet_key=wallet_key,
                to=to,
                amount=amount,
                contract=contract,
                config_override=config,
            )

        try:
            token = _transit()
        except Exception:
            self._repository.log_transaction(
                TransactionRecord(
                    wallet_id=wallet_id,
                    txid=None,
                    amount=amount,
                    coin=contract,
                    status="failed-transit",
                ),
            )
            raise
        self._repository.log_transaction(
            TransactionRecord(
                wallet_id=wallet_id,
                txid=token.token,
                amount=amount,
                coin=contract,
                status="pending-transit",
            ),
        )
        return token
