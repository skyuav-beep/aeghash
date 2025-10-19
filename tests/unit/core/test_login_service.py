from datetime import UTC, datetime
from typing import Dict, List, Optional

import pytest

from aeghash.core.auth_flow import AuthenticationResult
from aeghash.core.login_service import LoginError, LoginRequest, PasswordLoginService
from aeghash.core.repositories import (
    LoginAuditRecord,
    LoginAuditRepository,
    SessionRecord,
    SessionRepository,
    TwoFactorRecord,
    TwoFactorRepository,
    UserAccountRecord,
    UserAccountRepository,
    UserRecord,
    UserRepository,
)
from aeghash.core.two_factor import TwoFactorService
from aeghash.security.passwords import hash_password
from aeghash.utils import totp


class InMemoryAccountRepository(UserAccountRepository):
    def __init__(self) -> None:
        self.records: Dict[str, UserAccountRecord] = {}

    def save(self, record: UserAccountRecord) -> None:
        self.records[record.user_id] = record

    def find_by_email(self, email: str) -> Optional[UserAccountRecord]:
        return next((r for r in self.records.values() if r.email == email), None)

    def find(self, user_id: str) -> Optional[UserAccountRecord]:
        return self.records.get(user_id)


class InMemoryIdentityRepository(UserRepository):
    def __init__(self) -> None:
        self.records: Dict[tuple[str, str], UserRecord] = {}

    def find_by_oauth_identity(self, provider: str, subject: str) -> Optional[UserRecord]:
        return self.records.get((provider, subject))

    def create_identity(self, record: UserRecord) -> None:
        self.records[(record.provider, record.subject)] = record


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.records: List[SessionRecord] = []

    def create_session(self, record: SessionRecord) -> SessionRecord:
        self.records.append(record)
        return record


class InMemoryAuditRepository(LoginAuditRepository):
    def __init__(self) -> None:
        self.records: List[LoginAuditRecord] = []

    def log(self, record: LoginAuditRecord) -> None:
        self.records.append(record)


class InMemoryTwoFactorRepository(TwoFactorRepository):
    def __init__(self) -> None:
        self.records: Dict[str, TwoFactorRecord] = {}

    def get(self, user_id: str) -> Optional[TwoFactorRecord]:
        return self.records.get(user_id)

    def save(self, record: TwoFactorRecord) -> None:
        self.records[record.user_id] = record

    def disable(self, user_id: str) -> None:
        if user_id in self.records:
            self.records[user_id].enabled = False


class StubTurnstileVerifier:
    def __init__(self) -> None:
        self.calls: List[tuple[str, Optional[str]]] = []

    def verify(self, token: str, remote_ip: Optional[str]) -> None:
        self.calls.append((token, remote_ip))


def make_service(*, turnstile=None, two_factor=None):
    accounts = InMemoryAccountRepository()
    identities = InMemoryIdentityRepository()
    sessions = InMemorySessionRepository()
    audits = InMemoryAuditRepository()

    service = PasswordLoginService(
        accounts,
        identities,
        sessions,
        audits,
        two_factor_service=two_factor,
        turnstile_verifier=turnstile,
    )
    return service, accounts, identities, sessions, audits


def test_login_service_success() -> None:
    service, accounts, identities, sessions, audits = make_service()
    accounts.save(
        UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash=hash_password("strong-password"),
            is_active=True,
            created_at=datetime.now(UTC),
        ),
    )
    identities.create_identity(
        UserRecord(
            user_id="user-1",
            provider="local",
            subject="user@example.com",
            roles=("member",),
            two_factor_enabled=False,
        ),
    )

    result = service.login(LoginRequest(email="user@example.com", password="strong-password"))

    assert isinstance(result, AuthenticationResult)
    assert result.success is True
    assert result.user_id == "user-1"
    assert result.roles == ("member",)
    assert result.session_token
    assert audits.records[-1].status == "SUCCEEDED"
    assert sessions.records


def test_login_service_invalid_credentials() -> None:
    service, accounts, identities, sessions, audits = make_service()
    accounts.save(
        UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash=hash_password("strong-password"),
            is_active=True,
            created_at=datetime.now(UTC),
        ),
    )
    identities.create_identity(
        UserRecord(
            user_id="user-1",
            provider="local",
            subject="user@example.com",
            roles=("member",),
            two_factor_enabled=False,
        ),
    )

    with pytest.raises(LoginError):
        service.login(LoginRequest(email="user@example.com", password="wrong-password"))

    with pytest.raises(LoginError):
        service.login(LoginRequest(email="missing@example.com", password="strong-password"))

    assert audits.records[-1].status == "FAILED"


def test_login_service_inactive_account() -> None:
    service, accounts, identities, sessions, audits = make_service()
    accounts.save(
        UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash=hash_password("strong-password"),
            is_active=False,
            created_at=datetime.now(UTC),
        ),
    )
    identities.create_identity(
        UserRecord(
            user_id="user-1",
            provider="local",
            subject="user@example.com",
            roles=("member",),
            two_factor_enabled=False,
        ),
    )

    with pytest.raises(LoginError):
        service.login(LoginRequest(email="user@example.com", password="strong-password"))

    assert audits.records[-1].reason == "inactive_account"


def test_login_service_requires_turnstile_token() -> None:
    verifier = StubTurnstileVerifier()
    service, accounts, identities, sessions, audits = make_service(turnstile=verifier)
    accounts.save(
        UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash=hash_password("strong-password"),
            is_active=True,
            created_at=datetime.now(UTC),
        ),
    )
    identities.create_identity(
        UserRecord(
            user_id="user-1",
            provider="local",
            subject="user@example.com",
            roles=("member",),
            two_factor_enabled=False,
        ),
    )

    with pytest.raises(LoginError) as exc:
        service.login(LoginRequest(email="user@example.com", password="strong-password"))
    assert str(exc.value) == "turnstile_required"
    assert audits.records[-1].reason == "turnstile_missing"
    assert verifier.calls == []

    result = service.login(
        LoginRequest(
            email="user@example.com",
            password="strong-password",
            turnstile_token="token-123",
            remote_ip="127.0.0.1",
        ),
    )
    assert result.success is True
    assert verifier.calls == [("token-123", "127.0.0.1")]


def test_login_service_two_factor_challenge_flow() -> None:
    two_factor_repo = InMemoryTwoFactorRepository()
    two_factor = TwoFactorService(two_factor_repo)
    service, accounts, identities, sessions, audits = make_service(two_factor=two_factor)

    accounts.save(
        UserAccountRecord(
            user_id="user-1",
            email="user@example.com",
            password_hash=hash_password("strong-password"),
            is_active=True,
            created_at=datetime.now(UTC),
        ),
    )
    identities.create_identity(
        UserRecord(
            user_id="user-1",
            provider="local",
            subject="user@example.com",
            roles=("admin",),
            two_factor_enabled=True,
        ),
    )
    status = two_factor.enable("user-1")

    challenge = service.login(LoginRequest(email="user@example.com", password="strong-password"))
    assert challenge.success is False
    assert challenge.requires_two_factor is True
    assert audits.records[-1].status == "CHALLENGE"

    code = totp.totp(status.secret or "")
    success = service.login(
        LoginRequest(
            email="user@example.com",
            password="strong-password",
            two_factor_code=code,
        ),
    )
    assert success.success is True
    assert success.session_token
