from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aeghash.core.mining_service import WithdrawalRequest
from aeghash.core.mining_workflow import MiningWithdrawalOrchestrator, WithdrawalExecutionError
from aeghash.core.point_wallet import PointWalletService, WITHDRAWAL_STATUS_APPROVED_STAGE1
from aeghash.core.withdrawal_workflow import WithdrawalEvent, WithdrawalWorkflowService
from aeghash.utils.memory_repositories import (
    InMemoryPointWalletRepository,
    InMemoryWithdrawalAuditRepository,
    InMemoryRiskRepository,
)
from aeghash.security.risk import (
    RiskConfig,
    RiskRejected,
    RiskService,
    AmountLimitRule,
    IpReputationRule,
    DeviceNoveltyRule,
)


class StubMiningService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Decimal]] = []
        self.failures = 0

    def request_withdrawal(self, *, user_id: str, coin: str, amount: Decimal) -> WithdrawalRequest:
        if self.failures > 0:
            self.failures -= 1
            raise RuntimeError("HashDam unavailable")
        self.calls.append((user_id, coin, amount))
        return WithdrawalRequest(withdraw_id="hashdam-1", coin=coin, amount=amount)


class StubNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message) -> None:  # type: ignore[override]
        self.messages.append(f"{message.subject}: {message.body}")


@pytest.fixture()
def repository() -> InMemoryPointWalletRepository:
    return InMemoryPointWalletRepository()


@pytest.fixture()
def audit_repository() -> InMemoryWithdrawalAuditRepository:
    return InMemoryWithdrawalAuditRepository()


@pytest.fixture()
def risk_repository() -> InMemoryRiskRepository:
    return InMemoryRiskRepository()


@pytest.fixture()
def wallet_service(repository: InMemoryPointWalletRepository) -> PointWalletService:
    counter = 0

    def id_factory() -> str:
        nonlocal counter
        counter += 1
        return f"wid-{counter}"

    return PointWalletService(repository, id_factory=id_factory, clock=lambda: datetime(2025, 1, 1, tzinfo=UTC))


@pytest.fixture()
def workflow(
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
) -> WithdrawalWorkflowService:
    return WithdrawalWorkflowService(
        wallet_service,
        audit_repository,
        clock=lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
    )


@pytest.fixture()
def risk_service(risk_repository: InMemoryRiskRepository) -> RiskService:
    config = RiskConfig(
        amount_rule=AmountLimitRule(warn_limit=Decimal("50"), block_limit=Decimal("200")),
        ip_rule=IpReputationRule(blocked_ips=["198.51.100.10"], trusted_ips=["203.0.113.5"]),
        device_rule=DeviceNoveltyRule(review_limit=Decimal("60")),
    )
    return RiskService(risk_repository, config, clock=lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC))


@pytest.fixture()
def workflow_with_risk(
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    risk_service: RiskService,
) -> WithdrawalWorkflowService:
    return WithdrawalWorkflowService(
        wallet_service,
        audit_repository,
        clock=lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        risk_service=risk_service,
    )


@pytest.fixture()
def mining_service() -> StubMiningService:
    return StubMiningService()


@pytest.fixture()
def workflow_with_mining(
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    mining_service: StubMiningService,
) -> tuple[WithdrawalWorkflowService, StubNotifier, StubMiningService]:
    notifier = StubNotifier()
    orchestrator = MiningWithdrawalOrchestrator(mining_service, wallet_service, notifier=notifier)
    workflow = WithdrawalWorkflowService(
        wallet_service,
        audit_repository,
        clock=lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
        mining_orchestrator=orchestrator,
        two_step_required=True,
    )
    return workflow, notifier, mining_service


def test_request_withdrawal_logs_audit(
    workflow: WithdrawalWorkflowService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    wallet_service: PointWalletService,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("100"))

    snapshot = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("40"),
        requested_by="user-1",
        reference_id="order-1",
        metadata={"source": "order"},
        notes="initial request",
    )

    assert snapshot.status == "pending"
    record = audit_repository.records[-1]
    assert record.action == "requested"
    assert record.actor_id == "user-1"
    assert record.metadata == {"source": "order"}


def test_approve_withdrawal_logs_audit(
    workflow: WithdrawalWorkflowService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    wallet_service: PointWalletService,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("80"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("30"),
        requested_by="user-1",
    )

    snapshot = workflow.approve(request.request_id, approved_by="admin-1", notes="verified")

    assert snapshot.status == "approved"
    assert audit_repository.records[-1].action == "approved"
    assert audit_repository.records[-1].notes == "verified"


def test_reject_logs_entry(
    workflow: WithdrawalWorkflowService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    wallet_service: PointWalletService,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("60"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("20"),
        requested_by="user-1",
    )

    workflow.reject(request.request_id, rejected_by="admin-2", notes="kyc mismatch")

    actions = [record.action for record in audit_repository.records if record.request_id == request.request_id]
    assert actions == ["requested", "rejected"]


def test_cancel_logs_entry(
    workflow: WithdrawalWorkflowService,
    audit_repository: InMemoryWithdrawalAuditRepository,
    wallet_service: PointWalletService,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("40"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("15"),
        requested_by="user-1",
    )

    workflow.cancel(request.request_id, cancelled_by="user-1", notes="changed mind")

    actions = [record.action for record in audit_repository.records if record.request_id == request.request_id]
    assert actions == ["requested", "cancelled"]


def test_event_listener_receives_notifications(
    workflow: WithdrawalWorkflowService,
    wallet_service: PointWalletService,
) -> None:
    events: list[WithdrawalEvent] = []
    workflow.add_listener(events.append)

    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("50"))
    workflow.request_withdrawal(wallet_id=wallet.wallet_id, amount=Decimal("10"), requested_by="user-1")

    assert events
    assert events[0].action == "requested"


def test_list_audit_trail_returns_records(
    workflow: WithdrawalWorkflowService,
    wallet_service: PointWalletService,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("70"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("15"),
        requested_by="user-1",
    )
    workflow.approve(request.request_id, approved_by="admin-1")

    records = workflow.list_audit_trail(request.request_id)
    assert len(records) == 2
    assert records[0].action == "requested"
    assert records[1].action == "approved"


def test_mining_withdrawal_executes_hashdam(
    workflow_with_mining,
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
) -> None:
    workflow, notifier, mining_service = workflow_with_mining
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("90"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("30"),
        requested_by="user-1",
        metadata={"provider": "hashdam", "coin": "PEP"},
    )
    stage1 = workflow.approve(request.request_id, approved_by="admin-1", finalize=False)
    assert stage1.status == WITHDRAWAL_STATUS_APPROVED_STAGE1
    assert audit_repository.records[-1].action == "approved_stage1"

    snapshot = workflow.approve(request.request_id, approved_by="admin-2", finalize=True)

    assert snapshot.status == "approved"
    assert mining_service.calls == [("user-1", "PEP", Decimal("30"))]
    latest = audit_repository.records[-1]
    assert latest.action == "approved"
    assert latest.metadata and latest.metadata.get("hashdam_withdraw_id") == "hashdam-1"
    assert not notifier.messages


def test_mining_withdrawal_failure_marks_failed(
    workflow_with_mining,
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
) -> None:
    workflow, notifier, mining_service = workflow_with_mining
    mining_service.failures = 1
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("90"))
    request = workflow.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("30"),
        requested_by="user-1",
        metadata={"provider": "hashdam", "coin": "PEP"},
    )

    workflow.approve(request.request_id, approved_by="admin-1", finalize=False)

    with pytest.raises(WithdrawalExecutionError):
        workflow.approve(request.request_id, approved_by="admin-2", finalize=True)

    snapshot = wallet_service.get_withdrawal(request.request_id)
    assert snapshot.status == "failed"
    assert notifier.messages
    actions = [record.action for record in audit_repository.records if record.request_id == request.request_id]
    assert actions[-1] == "failed"


def test_risk_block_triggers_auto_cancel(
    workflow_with_risk: WithdrawalWorkflowService,
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("500"))
    with pytest.raises(RiskRejected):
        workflow_with_risk.request_withdrawal(
            wallet_id=wallet.wallet_id,
            amount=Decimal("250"),
            requested_by="user-1",
            ip_address="203.0.113.5",
            device_id="device-1",
        )

    actions = [record.action for record in audit_repository.records]
    assert actions[-1] == "cancelled"


def test_risk_review_logs_flag(
    workflow_with_risk: WithdrawalWorkflowService,
    wallet_service: PointWalletService,
    audit_repository: InMemoryWithdrawalAuditRepository,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("120"))
    workflow_with_risk.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("70"),
        requested_by="user-1",
        ip_address="198.51.100.20",
        device_id="device-unknown",
    )

    actions = [record.action for record in audit_repository.records]
    assert "flagged" in actions


def test_risk_events_recorded(
    workflow_with_risk: WithdrawalWorkflowService,
    wallet_service: PointWalletService,
    risk_repository: InMemoryRiskRepository,
) -> None:
    wallet = wallet_service.credit(user_id="user-1", amount=Decimal("120"))
    workflow_with_risk.request_withdrawal(
        wallet_id=wallet.wallet_id,
        amount=Decimal("70"),
        requested_by="user-1",
        ip_address="198.51.100.20",
        device_id="device-unknown",
    )

    events = risk_repository.events
    assert events
    assert events[-1].user_id == "user-1"
