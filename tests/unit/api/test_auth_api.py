from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

import pytest
from sqlalchemy import text

from aeghash.adapters.oauth import OAuthProfile, OAuthResult, OAuthToken
from aeghash.api import AuthenticationAPI, OAuthCallbackPayload
from aeghash.core.repositories import SessionRecord, TwoFactorRecord, UserRecord
from aeghash.core.two_factor import TwoFactorService
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.database import Base
from aeghash.infrastructure.repositories import SqlAlchemyTwoFactorRepository, UserIdentityModel
from aeghash.infrastructure.session import SessionManager
from aeghash.utils import totp


class StubTurnstileVerifier:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Optional[str]]] = []

    def verify(self, token: str, remote_ip: Optional[str]) -> None:
        self.calls.append((token, remote_ip))


class StubSessionManager:
    def __init__(self) -> None:
        self.session = object()

    @contextmanager
    def session_scope(self):
        yield self.session

    def dispose(self) -> None:  # pragma: no cover - not needed
        pass


class StubAuthService:
    def __init__(self, profile: OAuthProfile) -> None:
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
            profile=profile,
        )

    def authenticate(self, *, provider: str, code: str) -> OAuthResult:
        return self._result

    def close(self) -> None:  # pragma: no cover - not needed
        pass


class StubUserRepository:
    def find_by_oauth_identity(self, provider: str, subject: str) -> Optional[UserRecord]:
        if provider == "google" and subject == "subject-1":
            return UserRecord(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles=("member",),
                two_factor_enabled=False,
            )
        return None

    def create_identity(self, record: UserRecord) -> None:  # pragma: no cover - not used in these tests
        raise NotImplementedError


class StubSessionRepository:
    def __init__(self) -> None:
        self.records: list[SessionRecord] = []

    def create_session(self, record: SessionRecord) -> SessionRecord:
        self.records.append(record)
        return record


@dataclass
class StubSettings:
    database_url: str = "sqlite+pysqlite:///:memory:"


def make_container(turnstile_verifier):
    profile = OAuthProfile(provider="google", subject="subject-1", email=None, name=None, raw={})
    return ServiceContainer(
        settings=StubSettings(),  # type: ignore[arg-type]
        session_manager=StubSessionManager(),
        auth_service=StubAuthService(profile),
        turnstile_verifier=turnstile_verifier,
    )


def test_authentication_api_invokes_turnstile_verifier() -> None:
    verifier = StubTurnstileVerifier()
    container = make_container(verifier)
    session_repo = StubSessionRepository()

    api = AuthenticationAPI(
        container,
        user_repository_factory=lambda _session: StubUserRepository(),
        session_repository_factory=lambda _session: session_repo,
    )

    payload = OAuthCallbackPayload(
        provider="google",
        code="auth-code",
        state="abc",
        expected_state="abc",
        turnstile_token="turn-token",
    )

    result = api.authenticate(payload, remote_ip="1.1.1.1")

    assert result.success is True
    assert verifier.calls == [("turn-token", "1.1.1.1")]
    assert session_repo.records


def test_authentication_api_allows_missing_turnstile_in_dev_mode() -> None:
    container = make_container(turnstile_verifier=None)
    session_repo = StubSessionRepository()

    api = AuthenticationAPI(
        container,
        user_repository_factory=lambda _session: StubUserRepository(),
        session_repository_factory=lambda _session: session_repo,
    )

    payload = OAuthCallbackPayload(
        provider="google",
        code="auth-code",
        state="abc",
        expected_state="abc",
    )

    result = api.authenticate(payload)

    assert result.success is True
    assert session_repo.records and session_repo.records[0].roles == ("member",)


def test_authentication_api_raises_when_token_missing_but_turnstile_required() -> None:
    verifier = StubTurnstileVerifier()
    container = make_container(verifier)
    session_repo = StubSessionRepository()

    api = AuthenticationAPI(
        container,
        user_repository_factory=lambda _session: StubUserRepository(),
        session_repository_factory=lambda _session: session_repo,
    )

    payload = OAuthCallbackPayload(
        provider="google",
        code="auth-code",
        state="abc",
        expected_state="abc",
    )

    with pytest.raises(ValueError):
        api.authenticate(payload)


def test_authentication_api_from_container_with_sqlalchemy_repositories() -> None:
    session_manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_manager.engine)

    with session_manager.session_scope() as session:
        session.add(
            UserIdentityModel(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles="member",
                two_factor_enabled=False,
            ),
        )

    verifier = StubTurnstileVerifier()
    profile = OAuthProfile(provider="google", subject="subject-1", email=None, name=None, raw={})
    container = ServiceContainer(
        settings=StubSettings(),
        session_manager=session_manager,
        auth_service=StubAuthService(profile),
        turnstile_verifier=verifier,
    )

    api = AuthenticationAPI.from_container(container, include_two_factor=False)

    payload = OAuthCallbackPayload(
        provider="google",
        code="auth-code",
        state="abc",
        expected_state="abc",
        turnstile_token="turn-token",
    )

    result = api.authenticate(payload, remote_ip="5.5.5.5")

    assert result.success is True
    assert result.user_id == "user-1"
    assert result.roles == ("member",)
    assert verifier.calls == [("turn-token", "5.5.5.5")]

    with session_manager.session_scope() as session:
        inserted = session.execute(text("SELECT COUNT(*) FROM auth_sessions")).scalar()

    session_manager.dispose()

    assert inserted == 1


def test_authentication_api_from_container_enforces_two_factor() -> None:
    session_manager = SessionManager("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(session_manager.engine)

    with session_manager.session_scope() as session:
        session.add(
            UserIdentityModel(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles="member",
                two_factor_enabled=True,
            ),
        )
        repo = SqlAlchemyTwoFactorRepository(session)
        TwoFactorService(repo).enable("user-1")

    verifier = StubTurnstileVerifier()
    profile = OAuthProfile(provider="google", subject="subject-1", email=None, name=None, raw={})
    container = ServiceContainer(
        settings=StubSettings(),
        session_manager=session_manager,
        auth_service=StubAuthService(profile),
        turnstile_verifier=verifier,
    )

    api = AuthenticationAPI.from_container(container, include_two_factor=True)

    base_payload = {
        "provider": "google",
        "code": "auth-code",
        "state": "abc",
        "expected_state": "abc",
        "turnstile_token": "turn-token",
    }

    requires = api.authenticate(OAuthCallbackPayload(**base_payload))
    assert requires.success is False
    assert requires.requires_two_factor is True

    with session_manager.session_scope() as session:
        secret = session.execute(
            text("SELECT secret FROM two_factor_secrets WHERE user_id='user-1'"),
        ).scalar_one()

    payload_with_code = OAuthCallbackPayload(
        **base_payload,
        two_factor_code=totp.totp(secret),
    )

    success = api.authenticate(payload_with_code)
    assert success.success is True
    assert success.requires_two_factor is False

    session_manager.dispose()
