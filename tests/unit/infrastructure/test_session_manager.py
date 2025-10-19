from decimal import Decimal

import pytest

from aeghash.core.repositories import TransactionRecord, WalletRecord
from aeghash.infrastructure import Base
from aeghash.infrastructure.repositories import SqlAlchemyWalletRepository, TransactionModel, WalletModel
from aeghash.infrastructure.session import SessionManager


@pytest.fixture()
def session_manager() -> SessionManager:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)
    try:
        yield manager
    finally:
        manager.dispose()


def test_session_manager_commits(session_manager: SessionManager) -> None:
    with session_manager.session_scope() as session:
        repo = SqlAlchemyWalletRepository(session)
        repo.save_wallet(WalletRecord(user_id="user-1", address="0xabc", wallet_key="wallet"))
        repo.log_transaction(
            TransactionRecord(
                wallet_id="wallet-1",
                txid="tx123",
                amount=Decimal("1"),
                coin="BNB",
                status="submitted",
            ),
        )

    with session_manager.session_scope() as session:
        assert session.query(WalletModel).count() == 1
        assert session.query(TransactionModel).count() == 1


def test_session_manager_rolls_back(session_manager: SessionManager) -> None:
    with pytest.raises(ValueError):
        with session_manager.session_scope() as session:
            repo = SqlAlchemyWalletRepository(session)
            repo.save_wallet(WalletRecord(user_id="user-1", address="0xabc", wallet_key="wallet"))
            raise ValueError("force rollback")

    with session_manager.session_scope() as session:
        assert session.query(WalletModel).count() == 0
