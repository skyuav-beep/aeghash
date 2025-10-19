"""API facade for user signup operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from sqlalchemy.orm import Session

from aeghash.adapters.turnstile import TurnstileError
from aeghash.core.repositories import UserAccountRepository, UserRepository
from aeghash.core.signup_service import SignupError, SignupResult, SignupService
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.repositories import SqlAlchemyUserAccountRepository, SqlAlchemyUserRepository


@dataclass(slots=True)
class SignupPayload:
    email: str
    password: str
    roles: Sequence[str] | None = None
    turnstile_token: Optional[str] = None
    remote_ip: Optional[str] = None


class SignupAPI:
    """Wrap SignupService with container-managed repositories."""

    def __init__(
        self,
        container: ServiceContainer,
        *,
        account_repo_factory: Callable[[Session], UserAccountRepository],
        identity_repo_factory: Callable[[Session], UserRepository],
    ) -> None:
        self._container = container
        self._account_repo_factory = account_repo_factory
        self._identity_repo_factory = identity_repo_factory
        self._turnstile_verifier = container.turnstile_verifier

    def register(self, payload: SignupPayload) -> SignupResult:
        if self._turnstile_verifier:
            token = payload.turnstile_token
            if not token:
                raise SignupError("turnstile_required")
            try:
                self._turnstile_verifier.verify(token, payload.remote_ip)
            except TurnstileError as exc:
                raise SignupError("turnstile_failed") from exc

        with self._container.session_manager.session_scope() as session:
            accounts = self._account_repo_factory(session)
            identities = self._identity_repo_factory(session)
            service = SignupService(accounts, identities)
            return service.register(payload.email, payload.password, roles=payload.roles)

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "SignupAPI":
        return cls(
            container,
            account_repo_factory=lambda session: SqlAlchemyUserAccountRepository(session),
            identity_repo_factory=lambda session: SqlAlchemyUserRepository(session),
        )


__all__ = ["SignupAPI", "SignupPayload", "SignupError", "SignupResult"]
