from aeghash.core.repositories import UserRecord
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyUserRepository, UserIdentityModel
from aeghash.infrastructure.session import SessionManager


def test_user_repository_finds_user_by_provider_and_subject() -> None:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)

    with manager.session_scope() as session:
        session.add(
            UserIdentityModel(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles="member,admin",
                two_factor_enabled=True,
            ),
        )

    with manager.session_scope() as session:
        repo = SqlAlchemyUserRepository(session)
        record = repo.find_by_oauth_identity("google", "subject-1")

    manager.dispose()

    assert isinstance(record, UserRecord)
    assert record.user_id == "user-1"
    assert record.roles == ("member", "admin")
    assert record.two_factor_enabled is True


def test_user_repository_returns_none_for_missing_identity() -> None:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)

    with manager.session_scope() as session:
        repo = SqlAlchemyUserRepository(session)
        record = repo.find_by_oauth_identity("google", "missing")

    manager.dispose()

    assert record is None
