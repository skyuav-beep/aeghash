from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aeghash.core.mining_service import WithdrawalRequest
from aeghash.core.mining_workflow import MiningWithdrawalOrchestrator, WithdrawalExecutionError
from aeghash.core.point_wallet import PointWalletService, WITHDRAWAL_STATUS_FAILED
from aeghash.utils import InMemoryPointWalletRepository


class StubMiningService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Decimal]] = []

    def request_withdrawal(self, *, user_id: str, coin: str, amount: Decimal) -> WithdrawalRequest:
        self.calls.append((user_id, coin, amount))
        return WithdrawalRequest(withdraw_id="hashdam-1", coin=coin, amount=amount)


class FailingMiningService(StubMiningService):
    def request_withdrawal(self, *, user_id: str, coin: str, amount: Decimal) -> WithdrawalRequest:
        raise RuntimeError("HashDam unavailable")


@pytest.fixture()
def wallet_service() -> PointWalletService:
    repo = InMemoryPointWalletRepository()
    service = PointWalletService(repo, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))
    snapshot = service.ensure_wallet(user_id="user-1")
    service.credit(user_id="user-1", amount=Decimal("100"), reference_id="init")
    service.request_withdrawal(
        wallet_id=snapshot.wallet_id,
        amount=Decimal("50"),
        requested_by="user-1",
        metadata={"coin": "PEP"},
    )
    return service


def test_orchestrator_executes_hashdam_withdrawal(wallet_service: PointWalletService) -> None:
    mining = StubMiningService()
    orchestrator = MiningWithdrawalOrchestrator(mining, wallet_service)
    pending = wallet_service.list_withdrawals(wallet_id=wallet_service.get_wallet_by_user("user-1").wallet_id)[0]

    outcome = orchestrator.approve_and_execute(
        pending.request_id,
        approved_by="admin-1",
        notes="ok",
    )

    assert outcome.withdrawal.status == "approved"
    assert outcome.mining_request.coin == "PEP"
    assert mining.calls == [("user-1", "PEP", Decimal("50"))]


def test_orchestrator_marks_failure_on_exception(wallet_service: PointWalletService) -> None:
    mining = FailingMiningService()
    orchestrator = MiningWithdrawalOrchestrator(mining, wallet_service)
    pending = wallet_service.list_withdrawals(wallet_id=wallet_service.get_wallet_by_user("user-1").wallet_id)[0]

    with pytest.raises(WithdrawalExecutionError):
        orchestrator.approve_and_execute(pending.request_id, approved_by="admin-1")

    failed = wallet_service.get_withdrawal(pending.request_id)
    assert failed.status == WITHDRAWAL_STATUS_FAILED


def test_orchestrator_requires_coin_metadata(wallet_service: PointWalletService) -> None:
    repo = wallet_service._repository  # type: ignore[attr-defined]
    withdraw = repo.list_withdrawal_requests(wallet_id=wallet_service.get_wallet_by_user("user-1").wallet_id)[0]
    withdraw.metadata = {}
    repo.update_withdrawal_request(withdraw)
    mining = StubMiningService()
    orchestrator = MiningWithdrawalOrchestrator(mining, wallet_service)

    pending = wallet_service.list_withdrawals(wallet_id=wallet_service.get_wallet_by_user("user-1").wallet_id)[0]

    with pytest.raises(WithdrawalExecutionError):
        orchestrator.approve_and_execute(pending.request_id, approved_by="admin-1")
