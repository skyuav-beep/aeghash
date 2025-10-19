from datetime import UTC, datetime
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from aeghash.adapters.oauth import OAuthProfile, OAuthResult, OAuthToken
from aeghash.api.auth import OAuthCallbackPayload
from aeghash.api.http import create_http_app
from aeghash.application import Application, shutdown_application
from aeghash.core.auth_flow import AuthenticationResult
from aeghash.core.auth_service import AuthService
from aeghash.core.repositories import SessionRecord, UserAccountRecord, UserRecord
from aeghash.core.two_factor import TwoFactorService
from aeghash.infrastructure.audit import LoginAuditLogger
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import (
    SqlAlchemyLoginAuditRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTwoFactorRepository,
    SqlAlchemyUserAccountRepository,
    SqlAlchemyUserRepository,
    UserIdentityModel,
)
from aeghash.infrastructure.session import SessionManager
from aeghash.security.passwords import hash_password
from aeghash.utils import totp
from aeghash.utils.observability import AuthMetricCollector
from aeghash.config import (
    AppSettings,
    HashDamSettings,
    MBlockSettings,
    OAuthProviderSettings,
    OAuthSettings,
    TurnstileSettings,
)


@pytest.fixture(autouse=True)
def enable_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGHASH_DEV_MODE", "1")


class StubAuthenticationAPI:
    def __init__(self, result: AuthenticationResult | Exception) -> None:
        self.calls: list[tuple[OAuthCallbackPayload, str | None]] = []
        self._result = result

    def authenticate(self, payload: OAuthCallbackPayload, *, remote_ip: str | None = None) -> AuthenticationResult:
        self.calls.append((payload, remote_ip))
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def make_success_result() -> AuthenticationResult:
    return AuthenticationResult(
        success=True,
        user_id="user-1",
        roles=("member",),
        session_token="session-token",
        requires_two_factor=False,
    )


def test_oauth_callback_returns_result_and_invokes_api() -> None:
    app = create_http_app(shutdown_on_exit=False)
    stub = StubAuthenticationAPI(make_success_result())
    app.state.auth_api = stub

    with TestClient(app) as client:
        response = client.post(
            "/oauth/callback",
            json={
                "provider": "google",
                "code": "auth-code",
                "state": "state123",
                "expected_state": "state123",
                "turnstile_token": "turn-token",
            },
        )

    shutdown_application(app.state.application)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["user_id"] == "user-1"
    assert body["session_token"] == "session-token"
    assert stub.calls[0][0].provider == "google"
    assert stub.calls[0][1] == "testclient"


def test_oauth_callback_propagates_value_error_as_400() -> None:
    app = create_http_app(shutdown_on_exit=False)
    stub = StubAuthenticationAPI(ValueError("invalid turnstile token"))
    app.state.auth_api = stub

    with TestClient(app) as client:
        response = client.post(
            "/oauth/callback",
            json={
                "provider": "google",
                "code": "auth-code",
                "state": "state123",
                "expected_state": "state123",
            },
        )

    shutdown_application(app.state.application)

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid turnstile token"


class StubAuthService(AuthService):
    def __init__(self) -> None:
        self._result = OAuthResult(
            token=OAuthToken(
                access_token="token",
                token_type="Bearer",
                expires_in=3600,
                refresh_token=None,
                id_token=None,
                scope=None,
                raw={},
            ),
            profile=OAuthProfile(
                provider="google",
                subject="demo-subject",
                email="demo@example.com",
                name="Demo User",
                raw={},
            ),
        )

    def authenticate(self, *, provider: str, code: str) -> OAuthResult:
        if provider != "google":
            raise ValueError("Unknown provider")
        return self._result

    def close(self) -> None:  # pragma: no cover
        pass


class StubTurnstileVerifier:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def verify(self, token: str, remote_ip: str | None) -> None:
        self.calls.append((token, remote_ip))


def _make_settings(db_url: str) -> AppSettings:
    return AppSettings(
        hashdam=HashDamSettings(),
        mblock=MBlockSettings(base_url="http://dev-mblock", api_key="dev-key"),
        oauth=OAuthSettings(
            google=OAuthProviderSettings("id", "secret", "uri"),
            kakao=OAuthProviderSettings("id", "secret", "uri"),
            apple=OAuthProviderSettings("id", "secret", "uri"),
        ),
        turnstile=TurnstileSettings(secret_key="dev-turnstile"),
        database_url=db_url,
        secret_key="dev-secret",
    )


def _build_application(db_url: str, verifier: StubTurnstileVerifier) -> tuple[Application, str]:
    session_manager = SessionManager(db_url)
    Base.metadata.create_all(session_manager.engine)

    with session_manager.session_scope() as session:
        session.add(
            UserIdentityModel(
                user_id="admin-1",
                provider="google",
                subject="demo-subject",
                roles="admin,member",
                two_factor_enabled=True,
            ),
        )
        repo = SqlAlchemyTwoFactorRepository(session)
        status = TwoFactorService(repo).enable("admin-1")

    settings = _make_settings(db_url)

    container = ServiceContainer(
        settings=settings,
        session_manager=session_manager,
        auth_service=StubAuthService(),
        turnstile_client=None,
        turnstile_verifier=verifier,
    )
    application = Application(container=container, metrics=AuthMetricCollector())
    return application, status.secret or ""


def test_oauth_callback_two_factor_flow(tmp_path) -> None:
    db_path = tmp_path / "two_factor.db"
    db_url = f"sqlite+pysqlite:///{db_path}" 

    verifier = StubTurnstileVerifier()
    application, secret = _build_application(db_url, verifier)

    app = create_http_app(application=application, shutdown_on_exit=False, include_two_factor=True)

    with TestClient(app) as client:
        first = client.post(
            "/oauth/callback",
            json={
                "provider": "google",
                "code": "auth-code",
                "state": "state123",
                "expected_state": "state123",
                "turnstile_token": "turn-token",
            },
        )

        assert first.status_code == 200
        body_first = first.json()
        assert body_first["success"] is False
        assert body_first["requires_two_factor"] is True
        assert verifier.calls[-1] == ("turn-token", "testclient")

        code = totp.totp(secret)
        second = client.post(
            "/oauth/callback",
            json={
                "provider": "google",
                "code": "auth-code",
                "state": "state123",
                "expected_state": "state123",
                "turnstile_token": "turn-token",
                "two_factor_code": code,
            },
        )

    shutdown_application(app.state.application)

    assert second.status_code == 200
    body_second = second.json()
    assert body_second["success"] is True
    assert body_second["requires_two_factor"] is False

    manager = application.container.session_manager
    with manager.session_scope() as session:
        count = session.execute(text("SELECT COUNT(*) FROM auth_sessions")).scalar_one()
    assert count == 1


def _build_application_for_signup(db_url: str) -> tuple[Application, StubTurnstileVerifier]:
    verifier = StubTurnstileVerifier()
    session_manager = SessionManager(db_url)
    Base.metadata.create_all(session_manager.engine)

    container = ServiceContainer(
        settings=_make_settings(db_url),
        session_manager=session_manager,
        auth_service=StubAuthService(),
        turnstile_client=None,
        turnstile_verifier=verifier,
        audit_logger=LoginAuditLogger(session_manager),
    )
    # Wire audit logger to event hook similar to production bootstrap.
    def event_hook(name: str, payload: dict[str, object]) -> None:
        container.audit_logger.handle_event(name, payload)  # type: ignore[union-attr]

    container.event_hook = event_hook
    return Application(container=container, metrics=AuthMetricCollector()), verifier


def _seed_local_account(
    application: Application,
    *,
    email: str,
    password: str,
    active: bool = True,
    two_factor_enabled: bool = False,
    roles: tuple[str, ...] = ("member",),
) -> None:
    manager = application.container.session_manager
    with manager.session_scope() as session:
        account_repo = SqlAlchemyUserAccountRepository(session)
        identity_repo = SqlAlchemyUserRepository(session)
        account_repo.save(
            UserAccountRecord(
                user_id="user-1",
                email=email,
                password_hash=hash_password(password),
                is_active=active,
                created_at=datetime.now(UTC),
            ),
        )
        identity_repo.create_identity(
            UserRecord(
                user_id="user-1",
                provider="local",
                subject=email,
                roles=roles,
                two_factor_enabled=two_factor_enabled,
            ),
        )


def test_signup_endpoint_creates_account_and_identity(tmp_path) -> None:
    db_path = tmp_path / "signup.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        response = client.post(
            "/signup",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "password_confirm": "strong-password",
                "turnstile_token": "turn-123",
            },
        )

    shutdown_application(app.state.application)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["roles"] == ["member"]

    manager = application.container.session_manager
    with manager.session_scope() as session:
        account_repo = SqlAlchemyUserAccountRepository(session)
        identity_repo = SqlAlchemyUserRepository(session)
        account = account_repo.find_by_email("user@example.com")
        identity = identity_repo.find_by_oauth_identity("local", "user@example.com")
    assert account is not None
    assert identity is not None
    assert verifier.calls == [("turn-123", "testclient")]


def test_signup_endpoint_rejects_duplicate_email(tmp_path) -> None:
    db_path = tmp_path / "signup_dupe.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        first = client.post(
            "/signup",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "password_confirm": "strong-password",
                "turnstile_token": "turn-123",
            },
        )
        assert first.status_code == 201
        second = client.post(
            "/signup",
            json={
                "email": "user@example.com",
                "password": "another-password",
                "password_confirm": "another-password",
                "turnstile_token": "turn-456",
            },
        )

    shutdown_application(app.state.application)

    assert second.status_code == 400
    assert second.json()["detail"] == "email_already_exists"
    # Turnstile 검증은 두 번 호출되어야 한다.
    assert [call[0] for call in verifier.calls] == ["turn-123", "turn-456"]


def test_signup_requires_turnstile_token(tmp_path) -> None:
    db_path = tmp_path / "signup_turn_missing.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        response = client.post(
            "/signup",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "password_confirm": "strong-password",
            },
        )

    shutdown_application(app.state.application)

    assert response.status_code == 400
    assert response.json()["detail"] == "turnstile_required"
    assert verifier.calls == []


def test_password_login_endpoint(tmp_path) -> None:
    db_path = tmp_path / "login.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)
    _seed_local_account(
        application,
        email="user@example.com",
        password="strong-password",
        roles=("admin", "member"),
    )

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        response = client.post(
            "/login/password",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "turnstile_token": "turn-login",
            },
        )
        session_token = response.json()["session_token"]
        audit_response = client.get(
            "/audit/logins",
            headers={"Authorization": f"Bearer {session_token}"},
        )

    shutdown_application(app.state.application)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["user_id"] == "user-1"

    assert audit_response.status_code == 200
    audit_body = audit_response.json()
    assert audit_body
    statuses = {entry["status"] for entry in audit_body}
    assert "SUCCEEDED" in statuses

    manager = application.container.session_manager
    with manager.session_scope() as session:
        sessions = session.execute(text("SELECT COUNT(*) FROM auth_sessions")).scalar_one()
        audits = session.execute(text("SELECT COUNT(*) FROM login_audit_logs")).scalar_one()
    assert sessions == 1
    assert audits >= 2
    assert verifier.calls == [("turn-login", "testclient")]


def test_password_login_requires_turnstile_token(tmp_path) -> None:
    db_path = tmp_path / "login_turn_missing.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)
    _seed_local_account(application, email="user@example.com", password="strong-password")

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        response = client.post(
            "/login/password",
            json={"email": "user@example.com", "password": "strong-password"},
        )

    shutdown_application(app.state.application)

    assert response.status_code == 400
    assert response.json()["detail"] == "turnstile_required"
    assert verifier.calls == []


def test_audit_endpoint_requires_permission(tmp_path) -> None:
    db_path = tmp_path / "audit_auth.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, _ = _build_application_for_signup(db_url)

    app = create_http_app(application=application, shutdown_on_exit=False)

    manager = application.container.session_manager
    with manager.session_scope() as session:
        repo = SqlAlchemySessionRepository(session)
        repo.create_session(
            SessionRecord(
                token="member-token",
                user_id="user-99",
                roles=("member",),
                expires_at=time.time() + 3600,
            ),
        )

    with TestClient(app) as client:
        forbidden = client.get("/audit/logins", headers={"Authorization": "Bearer member-token"})

    shutdown_application(app.state.application)

    assert forbidden.status_code == 403
    assert forbidden.json()["detail"] == "forbidden"


def test_password_login_two_factor_flow(tmp_path) -> None:
    db_path = tmp_path / "login_2fa.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, verifier = _build_application_for_signup(db_url)
    _seed_local_account(
        application,
        email="user@example.com",
        password="strong-password",
        two_factor_enabled=True,
    )

    manager = application.container.session_manager
    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        status = TwoFactorService(repo).enable("user-1")

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        initial = client.post(
            "/login/password",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "turnstile_token": "turn-2fa",
            },
        )
        assert initial.status_code == 200
        initial_body = initial.json()
        assert initial_body["success"] is False
        assert initial_body["requires_two_factor"] is True

        code = totp.totp(status.secret or "")
        followup = client.post(
            "/login/password",
            json={
                "email": "user@example.com",
                "password": "strong-password",
                "turnstile_token": "turn-2fa",
                "two_factor_code": code,
            },
        )

    shutdown_application(app.state.application)

    assert followup.status_code == 200
    body = followup.json()
    assert body["success"] is True
    assert body["requires_two_factor"] is False

    with manager.session_scope() as session:
        session_count = session.execute(text("SELECT COUNT(*) FROM auth_sessions")).scalar_one()
    assert session_count == 1
    assert [call[0] for call in verifier.calls] == ["turn-2fa", "turn-2fa"]


def test_admin_two_factor_status_and_disable(tmp_path) -> None:
    db_path = tmp_path / "admin_two_factor.db"
    db_url = f"sqlite+pysqlite:///{db_path}"
    application, _ = _build_application_for_signup(db_url)

    manager = application.container.session_manager
    with manager.session_scope() as session:
        session_repo = SqlAlchemySessionRepository(session)
        session_repo.create_session(
            SessionRecord(
                token="admin-token",
                user_id="admin-1",
                roles=("admin",),
                expires_at=time.time() + 3600,
            ),
        )
        two_factor_repo = SqlAlchemyTwoFactorRepository(session)
        TwoFactorService(two_factor_repo).enable("user-123")

    app = create_http_app(application=application, shutdown_on_exit=False)

    with TestClient(app) as client:
        headers = {"Authorization": "Bearer admin-token"}

        status_response = client.get("/admin/users/user-123/two_factor", headers=headers)
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["enabled"] is True
        assert status_body["recovery_codes_remaining"] == 5

        disable_response = client.post("/admin/users/user-123/two_factor/disable", headers=headers)
        assert disable_response.status_code == 204

    shutdown_application(app.state.application)

    with manager.session_scope() as session:
        repo = SqlAlchemyTwoFactorRepository(session)
        record = repo.get("user-123")
        assert record is not None
        assert record.enabled is False
        assert record.recovery_codes == ()
        audit_rows = session.execute(text("SELECT status, reason FROM login_audit_logs"))
        statuses = [row[0] for row in audit_rows]
        assert "TWO_FACTOR_DISABLED" in statuses
