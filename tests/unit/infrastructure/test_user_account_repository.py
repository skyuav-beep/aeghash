from datetime import UTC, datetime

from aeghash.core.repositories import UserAccountRecord
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyUserAccountRepository
from aeghash.infrastructure.session import SessionManager


def test_user_account_repository_persists_and_loads_records() -> None:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)

    with manager.session_scope() as session:
        repo = SqlAlchemyUserAccountRepository(session)
        record = UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash="hash",
            is_active=True,
            created_at=datetime.now(UTC),
        )
        repo.save(record)

    with manager.session_scope() as session:
        repo = SqlAlchemyUserAccountRepository(session)
        fetched = repo.find_by_email("user@example.com")
        assert fetched is not None
        assert fetched.user_id == "user-1"
        assert fetched.is_active is True

    manager.dispose()


def test_user_account_repository_returns_none_when_missing() -> None:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)

    with manager.session_scope() as session:
        repo = SqlAlchemyUserAccountRepository(session)
        assert repo.find_by_email("missing@example.com") is None

    manager.dispose()
