from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from aeghash.core.point_wallet import PointWalletService
from aeghash.core.withdrawal_workflow import WithdrawalWorkflowService
from aeghash.infrastructure import (
    Base,
    SqlAlchemyPointWalletRepository,
    SqlAlchemyRiskRepository,
    SqlAlchemyWithdrawalAuditRepository,
)
from aeghash.infrastructure.repositories import RiskEventModel, WithdrawalAuditModel
from aeghash.infrastructure.session import SessionManager
from aeghash.security.risk import (
    AmountLimitRule,
    DeviceNoveltyRule,
    IpReputationRule,
    RiskConfig,
    RiskRejected,
    RiskService,
)


@pytest.fixture()
def session_manager() -> SessionManager:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)
    return manager


def _build_services(session):
    point_repo = SqlAlchemyPointWalletRepository(session)
    audit_repo = SqlAlchemyWithdrawalAuditRepository(session)
    risk_repo = SqlAlchemyRiskRepository(session)

    clock = lambda: datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    id_counter = {"value": 0}

    def id_factory() -> str:
        id_counter["value"] += 1
        return f"wid-{id_counter['value']}"

    event_counter = {"value": 0}

    def event_id_factory() -> str:
        event_counter["value"] += 1
        return f"evt-{event_counter['value']}"

    wallet_service = PointWalletService(point_repo, id_factory=id_factory, clock=clock)
    risk_service = RiskService(
        risk_repo,
        RiskConfig(
            amount_rule=AmountLimitRule(warn_limit=Decimal("75"), block_limit=Decimal("200")),
            ip_rule=IpReputationRule(blocked_ips=["198.51.100.10"]),
            device_rule=DeviceNoveltyRule(review_limit=Decimal("60")),
        ),
        clock=clock,
        event_id_factory=event_id_factory,
    )
    workflow = WithdrawalWorkflowService(
        wallet_service,
        audit_repo,
        clock=clock,
        risk_service=risk_service,
    )
    return workflow, wallet_service, risk_repo


def test_risk_blocking_auto_cancels_and_logs(session_manager: SessionManager) -> None:
    with session_manager.session_scope() as session:
        workflow, wallet_service, _ = _build_services(session)
        wallet = wallet_service.credit(user_id="user-1", amount=Decimal("300"))

        with pytest.raises(RiskRejected):
            workflow.request_withdrawal(
                wallet_id=wallet.wallet_id,
                amount=Decimal("250"),
                requested_by="user-1",
                ip_address="203.0.113.5",
                device_id="device-1",
            )

    with session_manager.session_scope() as session:
        audit_entries = list(session.execute(select(WithdrawalAuditModel)).scalars())
        statuses = [entry.action for entry in audit_entries]
        assert "cancelled" in statuses
        events = list(session.execute(select(RiskEventModel)).scalars())
        assert events


def test_risk_flag_records_events(session_manager: SessionManager) -> None:
    with session_manager.session_scope() as session:
        workflow, wallet_service, _ = _build_services(session)
        wallet = wallet_service.credit(user_id="user-1", amount=Decimal("120"))

        workflow.request_withdrawal(
            wallet_id=wallet.wallet_id,
            amount=Decimal("80"),
            requested_by="user-1",
            ip_address="198.51.100.20",
            device_id="device-new",
        )

    with session_manager.session_scope() as session:
        events = list(session.execute(select(RiskEventModel)).scalars())
        assert events
        assert events[0].category in {"amount_limit", "device_novelty"}
        audit_entries = list(session.execute(select(WithdrawalAuditModel)).scalars())
        actions = [entry.action for entry in audit_entries]
        assert "flagged" in actions
