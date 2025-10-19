"""API facade for password-based login."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from sqlalchemy.orm import Session

from aeghash.core.login_service import LoginError, LoginRequest, PasswordLoginService
from aeghash.core.repositories import (
    LoginAuditRepository,
    SessionRepository,
    TwoFactorRepository,
    UserAccountRepository,
    UserRepository,
)
from aeghash.core.two_factor import TwoFactorService
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.repositories import (
    SqlAlchemyLoginAuditRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTwoFactorRepository,
    SqlAlchemyUserAccountRepository,
    SqlAlchemyUserRepository,
)


@dataclass(slots=True)
class PasswordLoginPayload:
    email: str
    password: str
    turnstile_token: Optional[str] = None
    two_factor_code: Optional[str] = None
    remote_ip: Optional[str] = None


class PasswordLoginAPI:
    """Wrapper exposing password login via container-managed repositories."""

    def __init__(
        self,
        container: ServiceContainer,
        *,
        account_repo_factory: Callable[[Session], UserAccountRepository],
        identity_repo_factory: Callable[[Session], UserRepository],
        session_repo_factory: Callable[[Session], SessionRepository],
        audit_repo_factory: Callable[[Session], LoginAuditRepository],
        two_factor_repo_factory: Callable[[Session], TwoFactorRepository] | None = None,
    ) -> None:
        self._container = container
        self._account_repo_factory = account_repo_factory
        self._identity_repo_factory = identity_repo_factory
        self._session_repo_factory = session_repo_factory
        self._audit_repo_factory = audit_repo_factory
        self._two_factor_repo_factory = two_factor_repo_factory
        self._turnstile_verifier = container.turnstile_verifier

    def login(self, payload: PasswordLoginPayload):
        with self._container.session_manager.session_scope() as session:
            two_factor_service: TwoFactorService | None = None
            if self._two_factor_repo_factory:
                two_factor_service = TwoFactorService(
                    self._two_factor_repo_factory(session),
                    event_hook=self._container.event_hook,
                )

            service = PasswordLoginService(
                account_repository=self._account_repo_factory(session),
                identity_repository=self._identity_repo_factory(session),
                session_repository=self._session_repo_factory(session),
                audit_repository=self._audit_repo_factory(session),
                two_factor_service=two_factor_service,
                turnstile_verifier=self._turnstile_verifier,
            )
            request = LoginRequest(
                email=payload.email,
                password=payload.password,
                turnstile_token=payload.turnstile_token,
                remote_ip=payload.remote_ip,
                two_factor_code=payload.two_factor_code,
            )
            return service.login(request)

    @classmethod
    def from_container(cls, container: ServiceContainer) -> "PasswordLoginAPI":
        return cls(
            container,
            account_repo_factory=lambda session: SqlAlchemyUserAccountRepository(session),
            identity_repo_factory=lambda session: SqlAlchemyUserRepository(session),
            session_repo_factory=lambda session: SqlAlchemySessionRepository(session),
            audit_repo_factory=lambda session: SqlAlchemyLoginAuditRepository(session),
            two_factor_repo_factory=lambda session: SqlAlchemyTwoFactorRepository(session),
        )


__all__ = ["PasswordLoginAPI", "PasswordLoginPayload", "LoginError"]
