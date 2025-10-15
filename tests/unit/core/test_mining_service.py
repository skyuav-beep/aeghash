from decimal import Decimal

from aeghash.adapters.hashdam import AssetWithdrawal, HashBalance
from aeghash.core.mining_service import MiningService
from aeghash.core.repositories import MiningBalanceRecord, MiningRepository, WithdrawalRecord
from aeghash.utils import NotificationMessage, Notifier, RetryConfig


class StubHashDamClient:
    def __init__(self) -> None:
        self.balance_calls = 0
        self.withdrawals = []
        self.fail_withdrawal = False

    def get_hash_balance(self) -> HashBalance:
        self.balance_calls += 1
        return HashBalance(date="2025-08-15", credit=Decimal("10"), power=Decimal("100"))

    def request_asset_withdrawal(self, *, coin: str, amount: Decimal) -> AssetWithdrawal:
        if self.fail_withdrawal:
            raise ValueError("withdrawal failure")
        self.withdrawals.append({"coin": coin, "amount": amount})
        return AssetWithdrawal(withdraw_id="wd123", coin=coin, amount=amount)


class StubNotifier(Notifier):
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.messages.append(message)


class StubMiningRepository(MiningRepository):
    def __init__(self) -> None:
        self.balances: list[MiningBalanceRecord] = []
        self.withdrawals: list[WithdrawalRecord] = []

    def upsert_balance(self, record: MiningBalanceRecord) -> None:
        self.balances.append(record)

    def log_withdrawal(self, record: WithdrawalRecord) -> None:
        self.withdrawals.append(record)


def test_get_balance_uses_client() -> None:
    client = StubHashDamClient()
    repository = StubMiningRepository()
    service = MiningService(client, repository)

    balance = service.get_balance(user_id="user-1")

    assert balance.credit == Decimal("10")
    assert client.balance_calls == 1
    assert repository.balances[0].user_id == "user-1"


def test_request_withdrawal_returns_dataclass() -> None:
    client = StubHashDamClient()
    repository = StubMiningRepository()
    notifier = StubNotifier()
    service = MiningService(client, repository, notifier=notifier, retry_config=RetryConfig(attempts=2, initial_delay=0.01))

    result = service.request_withdrawal(user_id="user-1", coin="PEP", amount=Decimal("5"))

    assert result.withdraw_id == "wd123"
    assert client.withdrawals[0]["coin"] == "PEP"
    assert repository.withdrawals[0].user_id == "user-1"
    assert repository.withdrawals[0].status == "submitted"
    assert not notifier.messages


def test_request_withdrawal_failure_logs_status() -> None:
    client = StubHashDamClient()
    client.fail_withdrawal = True
    repository = StubMiningRepository()
    notifier = StubNotifier()
    service = MiningService(client, repository, notifier=notifier, retry_config=RetryConfig(attempts=2, initial_delay=0.01))

    try:
        service.request_withdrawal(user_id="user-1", coin="PEP", amount=Decimal("5"))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

    assert repository.withdrawals[0].status == "failed"
    assert repository.withdrawals[0].withdraw_id is None
    assert notifier.messages
