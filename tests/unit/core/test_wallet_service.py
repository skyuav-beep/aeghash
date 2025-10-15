from decimal import Decimal
from typing import Any, Optional

import pytest

from aeghash.adapters.mblock import TransitToken, TransferReceipt, WalletInfo
from aeghash.config import MBlockSettings
from aeghash.core.repositories import TransactionRecord, WalletRecord
from aeghash.core.wallet_service import WalletService
from aeghash.utils import NotificationMessage, Notifier, RetryConfig


class StubMBlockClient:
    def __init__(self) -> None:
        self.created_wallet = False
        self.transfers: list[dict[str, Any]] = []
        self.balance_calls: list[dict[str, Any]] = []
        self.transit_calls: list[dict[str, Any]] = []
        self.fail_transfer = False
        self.fail_transit = False

    def request_wallet(self) -> WalletInfo:
        self.created_wallet = True
        return WalletInfo(address="0xabc", wallet_key="wallet_key")

    def get_balance(self, *, address: str, contract: Optional[str] = None) -> Decimal:
        self.balance_calls.append({"address": address, "contract": contract})
        return Decimal("123.45")

    def transfer_by_wallet_key(
        self,
        *,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: Optional[str] = None,
    ) -> TransferReceipt:
        if self.fail_transfer:
            raise ValueError("transfer failure")
        self.transfers.append(
            {"wallet_key": wallet_key, "to": to, "amount": amount, "contract": contract},
        )
        return TransferReceipt(txid="tx123", message=None)

    def transit_by_wallet_key(
        self,
        *,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: str,
        config_override: Optional[dict[str, Any]] = None,
    ) -> TransitToken:
        if self.fail_transit:
            raise ValueError("transit failure")
        self.transit_calls.append(
            {
                "wallet_key": wallet_key,
                "to": to,
                "amount": amount,
                "contract": contract,
                "config": config_override,
            },
        )
        return TransitToken(token="token123", message=None)


class StubWalletRepository:
    def __init__(self) -> None:
        self.saved_wallets: list[WalletRecord] = []
        self.logged_transactions: list[TransactionRecord] = []

    def save_wallet(self, wallet: WalletRecord) -> None:
        self.saved_wallets.append(wallet)

    def log_transaction(self, transaction: TransactionRecord) -> None:
        self.logged_transactions.append(transaction)


@pytest.fixture()
def settings() -> MBlockSettings:
    return MBlockSettings(
        base_url="https://agent.mblockapi.com/bsc",
        api_key="secret",
        transit_fee=0.0002,
        transit_fee_wallet_key="fee_wallet",
        transit_callback_url="https://callback",
    )


def test_create_wallet(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    repository = StubWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    info = service.create_wallet(user_id="user-1")

    assert info.wallet_key == "wallet_key"
    assert client.created_wallet is True
    assert repository.saved_wallets[0].user_id == "user-1"


def test_transit_uses_default_config(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    repository = StubWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    service.request_transit(
        wallet_id="wallet-1",
        wallet_key="wallet_key",
        to="0xreceiver",
        amount=Decimal("1.5"),
        contract="0xcontract",
    )

    call = client.transit_calls[0]
    assert call["config"]["fee"] == settings.transit_fee
    assert call["config"]["feeWalletKey"] == settings.transit_fee_wallet_key
    assert call["config"]["callback"] == settings.transit_callback_url
    assert repository.logged_transactions[0].status == "pending-transit"


def test_transit_override_merges_config(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    repository = StubWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    service.request_transit(
        wallet_id="wallet-1",
        wallet_key="wallet_key",
        to="0xreceiver",
        amount=Decimal("1.5"),
        contract="0xcontract",
        override_config={"fee": 0.001, "delay": 5},
    )

    call = client.transit_calls[0]
    assert call["config"]["fee"] == 0.001
    assert call["config"]["delay"] == 5
    assert call["config"]["callback"] == settings.transit_callback_url


def test_transfer_logs_transaction(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    repository = StubWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    service.transfer_token(
        wallet_id="wallet-1",
        wallet_key="wallet_key",
        to="0xreceiver",
        amount=Decimal("2"),
        coin="BNB",
    )

    transaction = repository.logged_transactions[0]
    assert transaction.wallet_id == "wallet-1"
    assert transaction.coin == "BNB"
    assert transaction.status == "submitted"


def test_transfer_failure_logs_failed_status(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    client.fail_transfer = True
    repository = StubWalletRepository()
    notifier = StubNotifier()
    service = WalletService(
        client=client,
        settings=settings,
        repository=repository,
        notifier=notifier,
        retry_config=RetryConfig(attempts=2, initial_delay=0.01),
    )

    with pytest.raises(ValueError):
        service.transfer_token(
            wallet_id="wallet-1",
            wallet_key="wallet_key",
            to="0xreceiver",
            amount=Decimal("2"),
            coin="BNB",
        )

    assert repository.logged_transactions[0].status == "failed"
    assert repository.logged_transactions[0].txid is None
    assert notifier.messages


def test_transit_failure_logs_failed_status(settings: MBlockSettings) -> None:
    client = StubMBlockClient()
    client.fail_transit = True
    repository = StubWalletRepository()
    notifier = StubNotifier()
    service = WalletService(
        client=client,
        settings=settings,
        repository=repository,
        notifier=notifier,
        retry_config=RetryConfig(attempts=2, initial_delay=0.01),
    )

    with pytest.raises(ValueError):
        service.request_transit(
            wallet_id="wallet-1",
            wallet_key="wallet_key",
            to="0xreceiver",
            amount=Decimal("1.5"),
            contract="0xcontract",
        )

    assert repository.logged_transactions[0].status == "failed-transit"
    assert notifier.messages
class StubNotifier(Notifier):
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.messages.append(message)
