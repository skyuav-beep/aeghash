"""High-level API orchestration for OAuth authentication callbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from sqlalchemy.orm import Session

from aeghash.core.auth_flow import AuthenticationResult, OAuthFlowService, OAuthRequest
from aeghash.core.repositories import SessionRepository, TwoFactorRepository, UserRepository
from aeghash.core.two_factor import TwoFactorService
from aeghash.infrastructure.bootstrap import ServiceContainer
from aeghash.infrastructure.repositories import (
    SqlAlchemySessionRepository,
    SqlAlchemyTwoFactorRepository,
    SqlAlchemyUserRepository,
)


@dataclass(slots=True)
class OAuthCallbackPayload:
    """Incoming OAuth callback payload from the frontend."""

    provider: str
    code: str
    state: str
    expected_state: str
    turnstile_token: Optional[str] = None
    two_factor_code: Optional[str] = None


class AuthenticationAPI:
    """Facade for executing the OAuth flow using infrastructure services."""

    def __init__(
        self,
        container: ServiceContainer,
        *,
        user_repository_factory: Callable[[Session], UserRepository],
        session_repository_factory: Callable[[Session], SessionRepository],
        two_factor_repository_factory: Callable[[Session], TwoFactorRepository] | None = None,
    ) -> None:
        self._container = container
        self._user_repository_factory = user_repository_factory
        self._session_repository_factory = session_repository_factory
        self._two_factor_repository_factory = two_factor_repository_factory

    def authenticate(
        self,
        payload: OAuthCallbackPayload,
        *,
        remote_ip: Optional[str] = None,
    ) -> AuthenticationResult:
        """Process an OAuth callback and return the resulting authentication status."""

        with self._container.session_manager.session_scope() as session:
            user_repository = self._user_repository_factory(session)
            session_repository = self._session_repository_factory(session)
            two_factor_manager = self._build_two_factor_manager(session)

            flow = OAuthFlowService(
                self._container.auth_service,
                user_repository,
                session_repository,
                two_factor_manager=two_factor_manager,
                turnstile_verifier=self._container.turnstile_verifier,
            )

            request = OAuthRequest(
                provider=payload.provider,
                code=payload.code,
                state=payload.state,
                expected_state=payload.expected_state,
                two_factor_code=payload.two_factor_code,
                turnstile_token=payload.turnstile_token,
                turnstile_remote_ip=remote_ip,
            )
            return flow.authenticate(request)

    def _build_two_factor_manager(self, session: Session):
        if not self._two_factor_repository_factory:
            return None
        repository = self._two_factor_repository_factory(session)
        return TwoFactorService(repository, event_hook=self._container.event_hook)

    @classmethod
    def from_container(
        cls,
        container: ServiceContainer,
        *,
        include_two_factor: bool = True,
    ) -> AuthenticationAPI:
        """Create an AuthenticationAPI with default SQLAlchemy repositories."""

        def user_repo_factory(session: Session) -> UserRepository:
            return SqlAlchemyUserRepository(session)

        def session_repo_factory(session: Session) -> SessionRepository:
            return SqlAlchemySessionRepository(session)

        two_factor_factory: Callable[[Session], TwoFactorRepository] | None
        if include_two_factor:
            def factory(session: Session) -> TwoFactorRepository:
                return SqlAlchemyTwoFactorRepository(session)

            two_factor_factory = factory
        else:
            two_factor_factory = None

        return cls(
            container,
            user_repository_factory=user_repo_factory,
            session_repository_factory=session_repo_factory,
            two_factor_repository_factory=two_factor_factory,
        )
