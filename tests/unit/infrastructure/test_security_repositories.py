from sqlalchemy import text

from aeghash.core.repositories import SessionRecord, TwoFactorRecord
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemySessionRepository, SqlAlchemyTwoFactorRepository
from aeghash.infrastructure.session import SessionManager


def test_two_factor_repository_persists_records():
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)
    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        record = TwoFactorRecord(
            user_id="user-1",
            secret="secret",
            enabled=True,
            updated_at=0.0,
            recovery_codes=("hash-1", "hash-2"),
        )
        repo.save(record)
    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        stored = repo.get("user-1")
        assert stored and stored.enabled is True
        assert stored.recovery_codes == ("hash-1", "hash-2")
        repo.disable("user-1")
    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        stored = repo.get("user-1")
        assert stored and stored.enabled is False
        assert stored.recovery_codes == ()
    manager.dispose()


def test_session_repository_creates_session():
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)
    record = SessionRecord(token="token", user_id="user-1", roles=("member",), expires_at=123.0)
    with manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        repo.create_session(record)
    with manager.session_scope() as session:
        rows = session.execute(text("SELECT token, user_id FROM auth_sessions"))
        rows = rows.fetchall()
        assert rows[0][0] == "token"
        assert rows[0][1] == "user-1"
    with manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        stored = repo.get_session("token")
        assert stored is not None
        assert stored.user_id == "user-1"
        assert stored.roles == ("member",)
        assert stored.expires_at == 123.0
        missing = repo.get_session("missing")
        assert missing is None
    manager.dispose()
