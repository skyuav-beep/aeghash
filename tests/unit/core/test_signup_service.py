from datetime import UTC, datetime
from typing import Dict, Optional

import pytest

from aeghash.core.repositories import UserAccountRecord, UserRecord, UserRepository, UserAccountRepository
from aeghash.core.signup_service import SignupError, SignupService


class InMemoryAccountRepository(UserAccountRepository):
    def __init__(self) -> None:
        self.accounts: Dict[str, UserAccountRecord] = {}

    def save(self, record: UserAccountRecord) -> None:
        self.accounts[record.user_id] = record

    def find_by_email(self, email: str) -> Optional[UserAccountRecord]:
        for account in self.accounts.values():
            if account.email == email:
                return account
        return None

    def find(self, user_id: str) -> Optional[UserAccountRecord]:
        return self.accounts.get(user_id)


class InMemoryIdentityRepository(UserRepository):
    def __init__(self) -> None:
        self.identities: Dict[tuple[str, str], UserRecord] = {}

    def find_by_oauth_identity(self, provider: str, subject: str) -> Optional[UserRecord]:
        return self.identities.get((provider, subject))

    def create_identity(self, record: UserRecord) -> None:
        self.identities[(record.provider, record.subject)] = record


def test_signup_service_creates_account_and_identity() -> None:
    accounts = InMemoryAccountRepository()
    identities = InMemoryIdentityRepository()
    service = SignupService(accounts, identities, id_factory=lambda: "user-1")

    result = service.register("User@Example.com", "password123")

    assert result.user_id == "user-1"
    assert result.email == "user@example.com"
    assert result.roles == ("member",)

    stored_account = accounts.find("user-1")
    assert stored_account is not None
    assert stored_account.email == "user@example.com"
    assert stored_account.password_hash != "password123"

    identity = identities.find_by_oauth_identity("local", "user@example.com")
    assert identity is not None
    assert identity.roles == ("member",)


def test_signup_service_rejects_duplicate_email() -> None:
    accounts = InMemoryAccountRepository()
    identities = InMemoryIdentityRepository()
    service = SignupService(accounts, identities, id_factory=lambda: "user-1")
    service.register("user@example.com", "password123")

    with pytest.raises(SignupError) as exc:
        service.register("user@example.com", "differentpass")
    assert str(exc.value) == "email_already_exists"


def test_signup_service_rejects_invalid_email_or_short_password() -> None:
    accounts = InMemoryAccountRepository()
    identities = InMemoryIdentityRepository()
    service = SignupService(accounts, identities)

    with pytest.raises(SignupError):
        service.register("invalid-email", "password123")

    with pytest.raises(SignupError):
        service.register("user@example.com", "short")
