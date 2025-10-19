from datetime import UTC, datetime
import time

import pytest
from fastapi.testclient import TestClient

from aeghash.api.http import create_http_app
from aeghash.application import create_application, shutdown_application
from aeghash.core.repositories import LoginAuditRecord, SessionRecord
from aeghash.infrastructure import Base, SqlAlchemyLoginAuditRepository, SqlAlchemySessionRepository


@pytest.fixture()
def audit_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGHASH_DEV_MODE", "1")
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    app = create_application()
    container = app.container

    Base.metadata.create_all(container.session_manager.engine)

    with container.session_manager.session_scope() as session:
        repo = SqlAlchemyLoginAuditRepository(session)
        repo.log(
            LoginAuditRecord(
                provider="google",
                status="success",
                subject="john.doe@example.com",
                reason=None,
            ),
        )

    fastapi_app = create_http_app(app, shutdown_on_exit=False)
    client = TestClient(fastapi_app)
    yield client, container
    client.close()
    shutdown_application(app)


def _seed_session(container, token: str, roles: tuple[str, ...]) -> None:
    with container.session_manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        repo.create_session(
            SessionRecord(
                token=token,
                user_id="user-1",
                roles=roles,
                expires_at=time.time() + 3600,
            ),
        )


def test_login_audit_masking_for_support(audit_client):
    client, container = audit_client
    _seed_session(container, "support-token", ("support",))

    response = client.get(
        "/audit/logins",
        headers={"Authorization": "Bearer support-token"},
    )

    assert response.status_code == 200
    records = response.json()
    assert records[0]["subject"].startswith("jo")
    assert "@example.com" in records[0]["subject"]
    assert "***" in records[0]["subject"]


def test_login_audit_full_subject_for_admin(audit_client):
    client, container = audit_client
    _seed_session(container, "admin-token", ("admin",))

    response = client.get(
        "/audit/logins",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    records = response.json()
    assert records[0]["subject"] == "john.doe@example.com"
