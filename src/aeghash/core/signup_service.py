"""Signup service for local user registration."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, Sequence

from aeghash.core.repositories import UserAccountRecord, UserAccountRepository, UserRecord, UserRepository
from aeghash.security.passwords import hash_password


DEFAULT_ROLES: tuple[str, ...] = ("member",)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupError(ValueError):
    """Raised when signup input is invalid or conflicts with existing data."""


@dataclass(slots=True)
class SignupResult:
    user_id: str
    email: str
    roles: tuple[str, ...]


class SignupService:
    """Register new local user accounts with hashed passwords."""

    def __init__(
        self,
        account_repository: UserAccountRepository,
        identity_repository: UserRepository,
        *,
        id_factory: Callable[[], str] | None = None,
        default_roles: Sequence[str] = DEFAULT_ROLES,
    ) -> None:
        self._accounts = account_repository
        self._identities = identity_repository
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._default_roles = tuple(default_roles)

    def register(self, email: str, password: str, *, roles: Sequence[str] | None = None) -> SignupResult:
        normalized_email = self._normalize_email(email)
        if not normalized_email:
            raise SignupError("invalid_email")
        if len(password) < 8:
            raise SignupError("password_too_short")

        if self._accounts.find_by_email(normalized_email) is not None:
            raise SignupError("email_already_exists")

        user_id = self._id_factory()
        password_hash = hash_password(password)
        timestamp = datetime.now(UTC)
        account_record = UserAccountRecord(
            user_id=user_id,
            email=normalized_email,
            password_hash=password_hash,
            is_active=True,
            created_at=timestamp,
        )
        self._accounts.save(account_record)

        identity_roles = tuple(roles) if roles else self._default_roles
        identity_record = UserRecord(
            user_id=user_id,
            provider="local",
            subject=normalized_email,
            roles=identity_roles,
            two_factor_enabled=False,
        )
        self._identities.create_identity(identity_record)

        return SignupResult(user_id=user_id, email=normalized_email, roles=identity_roles)

    @staticmethod
    def _normalize_email(email: str) -> str:
        candidate = email.strip().lower()
        if not candidate or not EMAIL_REGEX.match(candidate):
            return ""
        return candidate
