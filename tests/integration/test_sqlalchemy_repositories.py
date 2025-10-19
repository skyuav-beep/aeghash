from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from aeghash.adapters.hashdam import HashBalance
from aeghash.core.repositories import (
    MiningBalanceRecord,
    PointLedgerRecord,
    PointWalletRecord,
    RiskEventRecord,
    TransactionRecord,
    WalletRecord,
    WithdrawalAuditRecord,
    KnownDeviceRecord,
    WithdrawalRecord,
    WithdrawalRequestRecord,
    OrganizationNodeRecord,
    SpilloverLogRecord,
    BonusEntryRecord,
    OrderRecord,
    IdempotencyKeyRecord,
)
from aeghash.infrastructure import (
    Base,
    SqlAlchemyMiningRepository,
    SqlAlchemyPointWalletRepository,
    SqlAlchemyWithdrawalAuditRepository,
    SqlAlchemyRiskRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyBonusRepository,
    SqlAlchemyWalletRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyIdempotencyRepository,
    create_engine_and_session,
)
from aeghash.infrastructure.repositories import (
    MiningBalanceModel,
    PointLedgerModel,
    PointWalletModel,
    PointWithdrawalModel,
    RiskEventModel,
    RiskKnownDeviceModel,
    OrganizationNodeModel,
    SpilloverLogModel,
    BonusEntryModel,
    TransactionModel,
    WalletModel,
    WithdrawalModel,
    WithdrawalAuditModel,
    OrderModel,
    IdempotencyKeyModel,
)
from aeghash.core.point_wallet import WITHDRAWAL_STATUS_PENDING


@pytest.fixture()
def session() -> Session:
    engine, SessionLocal = create_engine_and_session("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_sqlalchemy_wallet_repository(session: Session) -> None:
    repo = SqlAlchemyWalletRepository(session)
    repo.save_wallet(WalletRecord(user_id="user-1", address="0xabc", wallet_key="wallet"))
    repo.log_transaction(
        TransactionRecord(
            wallet_id="wallet-1",
            txid="tx123",
            amount=Decimal("1.0"),
            coin="BNB",
            status="submitted",
        ),
    )
    session.commit()

    assert session.query(WalletModel).count() == 1
    tx = session.query(TransactionModel).one()
    assert tx.status == "submitted"


def test_sqlalchemy_order_repository(session: Session) -> None:
    repo = SqlAlchemyOrderRepository(session)
    now = datetime.now(UTC)
    record = OrderRecord(
        order_id="order-1",
        user_id="user-1",
        total_amount=Decimal("200"),
        pv_amount=Decimal("150"),
        status="PAID",
        channel="ONLINE",
        metadata={"source": "test"},
        created_at=now,
    )
    repo.upsert_order(record)
    session.commit()

    db_order = session.query(OrderModel).filter_by(order_id="order-1").one()
    assert db_order.total_amount == Decimal("200")

    fetched = repo.get_order("order-1")
    assert fetched is not None
    assert fetched.total_amount == Decimal("200")


def test_sqlalchemy_idempotency_repository(session: Session) -> None:
    repo = SqlAlchemyIdempotencyRepository(session)
    now = datetime.now(UTC)
    record = IdempotencyKeyRecord(
        key="idem-1",
        scope="aegmall:user-1",
        payload_hash="hash-1",
        status="PENDING",
        created_at=now,
        expires_at=now,
    )
    assert repo.create(record) is True
    assert repo.create(record) is False

    fetched = repo.get(key="idem-1", scope="aegmall:user-1")
    assert fetched is not None
    repo.mark_status(key="idem-1", scope="aegmall:user-1", status="SUCCEEDED", resource_id="order-1")
    session.commit()

    db_record = session.query(IdempotencyKeyModel).filter_by(key="idem-1").one()
    assert db_record.status == "SUCCEEDED"
    assert db_record.resource_id == "order-1"


def test_sqlalchemy_mining_repository(session: Session) -> None:
    repo = SqlAlchemyMiningRepository(session)
    repo.upsert_balance(
        MiningBalanceRecord(
            user_id="user-1",
            balance=HashBalance(date="2025-08-15", credit=Decimal("10"), power=Decimal("100")),
        ),
    )
    repo.log_withdrawal(
        WithdrawalRecord(
            user_id="user-1",
            withdraw_id="wd123",
            coin="PEP",
            amount=Decimal("5"),
            status="submitted",
        ),
    )
    session.commit()

    credit = session.query(MiningBalanceModel).filter_by(user_id="user-1").one().credit
    assert credit == Decimal("10")
    withdrawal = session.query(WithdrawalModel).one()
    assert withdrawal.status == "submitted"


def test_sqlalchemy_point_wallet_repository(session: Session) -> None:
    repo = SqlAlchemyPointWalletRepository(session)
    now = datetime.now(UTC)
    wallet_record = PointWalletRecord(
        wallet_id="wallet-pt-1",
        user_id="user-pt-1",
        balance=Decimal("0"),
        pending_withdrawal=Decimal("0"),
        status="active",
        created_at=now,
        updated_at=now,
    )
    persisted = repo.create_wallet(wallet_record)
    assert persisted.wallet_id == "wallet-pt-1"

    persisted.balance = Decimal("150")
    persisted.updated_at = now
    repo.update_wallet(persisted)

    repo.add_ledger_entry(
        PointLedgerRecord(
            entry_id="ledger-1",
            wallet_id="wallet-pt-1",
            entry_type="credit",
            amount=Decimal("150"),
            balance_after=Decimal("150"),
            pending_after=Decimal("0"),
            reference_id=None,
            metadata=None,
            created_at=now,
        ),
    )

    withdrawal = repo.create_withdrawal_request(
        WithdrawalRequestRecord(
            request_id="wd-pt-1",
            wallet_id="wallet-pt-1",
            amount=Decimal("40"),
            status=WITHDRAWAL_STATUS_PENDING,
            requested_by="user-pt-1",
            reference_id="ref-1",
            metadata={"source": "test"},
            created_at=now,
        ),
    )
    assert withdrawal.status == WITHDRAWAL_STATUS_PENDING

    session.commit()

    db_wallet = session.query(PointWalletModel).filter_by(wallet_id="wallet-pt-1").one()
    assert db_wallet.balance == Decimal("150")
    assert session.query(PointLedgerModel).count() == 1
    assert session.query(PointWithdrawalModel).count() == 1


def test_sqlalchemy_withdrawal_audit_repository(session: Session) -> None:
    repo = SqlAlchemyWithdrawalAuditRepository(session)
    record = WithdrawalAuditRecord(
        request_id="wd-pt-1",
        wallet_id="wallet-pt-1",
        action="approved",
        actor_id="admin-1",
        amount=Decimal("40"),
        status="approved",
        notes="checked",
        metadata={"source": "test"},
        created_at=datetime.now(UTC),
    )
    repo.log(record)
    session.commit()

    results = repo.list_for_request("wd-pt-1")
    assert results[0].action == "approved"
    assert session.query(WithdrawalAuditModel).count() == 1


def test_sqlalchemy_risk_repository(session: Session) -> None:
    repo = SqlAlchemyRiskRepository(session)
    now = datetime.now(UTC)
    repo.record_event(
        RiskEventRecord(
            event_id="evt-1",
            user_id="user-1",
            category="amount_limit",
            severity="review",
            message="Review required",
            attributes={"amount": "70"},
            created_at=now,
        ),
    )
    repo.upsert_known_device(
        KnownDeviceRecord(
            user_id="user-1",
            device_id="device-1",
            first_seen=now,
            last_seen=now,
        ),
    )
    session.commit()

    events = repo.list_recent("user-1")
    assert events and events[0].category == "amount_limit"
    device = repo.get_known_device("user-1", "device-1")
    assert device is not None
    assert session.query(RiskEventModel).count() == 1
    assert session.query(RiskKnownDeviceModel).count() == 1


def test_sqlalchemy_organization_repository(session: Session) -> None:
    repo = SqlAlchemyOrganizationRepository(session)
    now = datetime.now(UTC)
    root = repo.create_node(
        OrganizationNodeRecord(
            node_id="node-root",
            user_id="root",
            tree_type="binary",
            parent_node_id=None,
            sponsor_user_id=None,
            position=None,
            depth=0,
            path="/node-root",
            created_at=now,
            updated_at=now,
        ),
    )
    child = repo.create_node(
        OrganizationNodeRecord(
            node_id="node-child",
            user_id="child",
            tree_type="binary",
            parent_node_id=root.node_id,
            sponsor_user_id="root",
            position="L",
            depth=1,
            path=f"{root.path}/node-child",
            created_at=now,
            updated_at=now,
        ),
    )
    repo.log_spillover(
        SpilloverLogRecord(
            log_id="spill-1",
            tree_type="binary",
            sponsor_user_id="root",
            assigned_user_id="child",
            parent_node_id=root.node_id,
            position="L",
            created_at=now,
        ),
    )
    session.commit()

    db_node = session.query(OrganizationNodeModel).filter_by(node_id="node-child").one()
    assert db_node.parent_node_id == root.node_id
    spills = session.query(SpilloverLogModel).filter_by(sponsor_user_id="root").count()
    assert spills == 1


def test_sqlalchemy_bonus_repository(session: Session) -> None:
    repo = SqlAlchemyBonusRepository(session)
    record = BonusEntryRecord(
        bonus_id="bonus-1",
        user_id="root",
        source_user_id="member",
        bonus_type="recommend",
        order_id="order-1",
        level=1,
        pv_amount=Decimal("100"),
        bonus_amount=Decimal("30"),
        status="PENDING",
        metadata={"order_id": "order-1"},
        created_at=datetime.now(UTC),
    )
    repo.record_bonus(record)
    session.commit()

    pending = repo.list_pending()
    assert pending[0].bonus_type == "recommend"
    assert session.query(BonusEntryModel).count() == 1
