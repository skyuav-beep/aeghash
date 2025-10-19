from dataclasses import dataclass
from typing import Optional

import pytest

from aeghash.adapters.oauth import OAuthProfile, OAuthResult, OAuthToken
from aeghash.core.auth_flow import AuthenticationResult, OAuthFlowService, OAuthRequest
from aeghash.core.auth_service import AuthService, OAuthClient
from aeghash.core.repositories import SessionRecord, SessionRepository, UserRecord, UserRepository


@dataclass
class StubSession(SessionRecord):
    pass


class StubSessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.records: list[SessionRecord] = []

    def create_session(self, record: SessionRecord) -> SessionRecord:
        self.records.append(record)
        return record


class StubUserRepository(UserRepository):
    def __init__(self, users: dict[tuple[str, str], UserRecord]) -> None:
        self._users = users

    def find_by_oauth_identity(self, provider: str, subject: str) -> Optional[UserRecord]:
        return self._users.get((provider, subject))

    def create_identity(self, record: UserRecord) -> None:  # pragma: no cover - not used in these tests
        self._users[(record.provider, record.subject)] = record


class StubOAuthClient(OAuthClient):
    provider_name = "google"

    def __init__(self, result: OAuthResult) -> None:
        self._result = result

    def authenticate(self, *, code: str) -> OAuthResult:
        return self._result

    def close(self) -> None:
        pass


class StubAuthService(AuthService):
    def __init__(self, result: OAuthResult) -> None:
        super().__init__({"google": StubOAuthClient(result)})


class StubTwoFactorManager:
    def __init__(self, enabled_users: set[str], valid_codes: dict[str, str]) -> None:
        self.enabled_users = enabled_users
        self.valid_codes = valid_codes
        self.initiated: list[str] = []

    def is_enabled(self, user_id: str) -> bool:
        return user_id in self.enabled_users

    def initiate_challenge(self, user_id: str) -> None:
        self.initiated.append(user_id)

    def verify_code(self, user_id: str, code: str) -> bool:
        return self.valid_codes.get(user_id) == code


class StubTurnstileManager:
    def __init__(self, should_pass: bool = True) -> None:
        self.should_pass = should_pass
        self.calls: list[tuple[str, Optional[str]]] = []

    def verify(self, token: str, remote_ip: Optional[str]) -> None:
        self.calls.append((token, remote_ip))
        if not self.should_pass:
            raise ValueError("turnstile failure")


def make_oauth_result(subject: str) -> OAuthResult:
    return OAuthResult(
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
            subject=subject,
            email="user@example.com",
            name="User",
            raw={},
        ),
    )


def test_oauth_flow_success_without_two_factor() -> None:
    result = make_oauth_result("subject-1")
    auth_service = StubAuthService(result)
    sessions = StubSessionRepository()
    users = StubUserRepository(
        {("google", "subject-1"): UserRecord(user_id="user-1", provider="google", subject="subject-1", roles=("member",))},
    )
    turnstile = StubTurnstileManager()
    flow = OAuthFlowService(auth_service, users, sessions, turnstile_verifier=turnstile)

    outcome = flow.authenticate(
        OAuthRequest(
            provider="google",
            code="auth-code",
            state="abc",
            expected_state="abc",
            turnstile_token="token",
            turnstile_remote_ip="1.1.1.1",
        ),
    )

    assert isinstance(outcome, AuthenticationResult)
    assert outcome.success is True
    assert outcome.session_token is not None
    assert sessions.records
    assert turnstile.calls == [("token", "1.1.1.1")]


def test_oauth_flow_state_mismatch_raises() -> None:
    result = make_oauth_result("subject-1")
    flow = OAuthFlowService(StubAuthService(result), StubUserRepository({}), StubSessionRepository())

    with pytest.raises(ValueError):
        flow.authenticate(OAuthRequest(provider="google", code="auth-code", state="abc", expected_state="xyz"))


def test_oauth_flow_user_not_found() -> None:
    result = make_oauth_result("missing")
    flow = OAuthFlowService(StubAuthService(result), StubUserRepository({}), StubSessionRepository())

    with pytest.raises(ValueError):
        flow.authenticate(OAuthRequest(provider="google", code="auth-code", state="abc", expected_state="abc"))


def test_oauth_flow_requires_two_factor_when_enabled() -> None:
    result = make_oauth_result("subject-1")
    auth_service = StubAuthService(result)
    sessions = StubSessionRepository()
    users = StubUserRepository(
        {
            ("google", "subject-1"): UserRecord(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles=("member",),
                two_factor_enabled=True,
            ),
        },
    )
    manager = StubTwoFactorManager({"user-1"}, {"user-1": "654321"})
    flow = OAuthFlowService(auth_service, users, sessions, two_factor_manager=manager)

    outcome = flow.authenticate(
        OAuthRequest(provider="google", code="auth-code", state="abc", expected_state="abc"),
    )

    assert outcome.success is False
    assert outcome.requires_two_factor is True
    assert manager.initiated == ["user-1"]
    assert not sessions.records


def test_oauth_flow_two_factor_verification_success() -> None:
    result = make_oauth_result("subject-1")
    auth_service = StubAuthService(result)
    sessions = StubSessionRepository()
    users = StubUserRepository(
        {
            ("google", "subject-1"): UserRecord(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles=("member",),
                two_factor_enabled=True,
            ),
        },
    )
    manager = StubTwoFactorManager({"user-1"}, {"user-1": "654321"})
    flow = OAuthFlowService(auth_service, users, sessions, two_factor_manager=manager)

    outcome = flow.authenticate(
        OAuthRequest(
            provider="google",
            code="auth-code",
            state="abc",
            expected_state="abc",
            two_factor_code="654321",
        ),
    )

    assert outcome.success is True
    assert outcome.session_token is not None
    assert manager.initiated == []
    assert sessions.records


def test_oauth_flow_two_factor_invalid_code_raises() -> None:
    result = make_oauth_result("subject-1")
    auth_service = StubAuthService(result)
    sessions = StubSessionRepository()
    users = StubUserRepository(
        {
            ("google", "subject-1"): UserRecord(
                user_id="user-1",
                provider="google",
                subject="subject-1",
                roles=("member",),
                two_factor_enabled=True,
            ),
        },
    )
    manager = StubTwoFactorManager({"user-1"}, {"user-1": "654321"})
    flow = OAuthFlowService(auth_service, users, sessions, two_factor_manager=manager)

    with pytest.raises(ValueError):
        flow.authenticate(
            OAuthRequest(
                provider="google",
                code="auth-code",
                state="abc",
                expected_state="abc",
                two_factor_code="123456",
            ),
        )


def test_oauth_flow_missing_turnstile_token_raises() -> None:
    result = make_oauth_result("subject-1")
    auth_service = StubAuthService(result)
    sessions = StubSessionRepository()
    users = StubUserRepository(
        {("google", "subject-1"): UserRecord(user_id="user-1", provider="google", subject="subject-1", roles=("member",))},
    )
    turnstile = StubTurnstileManager()
    flow = OAuthFlowService(auth_service, users, sessions, turnstile_verifier=turnstile)

    with pytest.raises(ValueError):
        flow.authenticate(OAuthRequest(provider="google", code="auth-code", state="abc", expected_state="abc"))
