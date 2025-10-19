from aeghash.infrastructure.audit import LoginAuditLogger
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import LoginAuditModel, SqlAlchemyLoginAuditRepository
from aeghash.infrastructure.session import SessionManager


def test_login_audit_logger_persists_events() -> None:
    manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(manager.engine)
    logger = LoginAuditLogger(manager)

    logger.handle_event("auth.start", {"provider": "google"})
    logger.handle_event("auth.success", {"provider": "google", "subject": "user-123"})
    logger.handle_event("auth.error", {"provider": "kakao", "reason": "invalid_code"})

    with manager.session_scope() as session:
        repo = SqlAlchemyLoginAuditRepository(session)
        entries = session.query(LoginAuditModel).order_by(LoginAuditModel.id).all()
        recent = repo.list_recent(limit=2)

    assert len(entries) == 3
    assert entries[0].status == "STARTED"
    assert entries[1].status == "SUCCEEDED"
    assert entries[1].subject == "user-123"
    assert entries[2].status == "FAILED"
    assert entries[2].reason == "invalid_code"

    assert len(recent) == 2
    statuses = {entry.status for entry in recent}
    assert "SUCCEEDED" in statuses
    manager.dispose()
