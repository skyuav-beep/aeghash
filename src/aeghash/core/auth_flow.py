"""High-level OAuth authentication flow handling."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Optional, Protocol

from aeghash.core.auth_service import AuthService
from aeghash.core.repositories import SessionRecord, SessionRepository, UserRecord, UserRepository


class TwoFactorManager(Protocol):
    """Protocol for managing second-factor challenges."""

    def is_enabled(self, user_id: str) -> bool:
        ...

    def initiate_challenge(self, user_id: str) -> None:
        ...

    def verify_code(self, user_id: str, code: str) -> bool:
        ...


class TurnstileManager(Protocol):
    """Protocol for verifying Turnstile challenge tokens."""

    def verify(self, token: str, remote_ip: Optional[str]) -> None:
        ...


@dataclass(slots=True)
class OAuthRequest:
    """Data required to process an OAuth callback."""

    provider: str
    code: str
    state: str
    expected_state: str
    two_factor_code: Optional[str] = None
    turnstile_token: Optional[str] = None
    turnstile_remote_ip: Optional[str] = None


@dataclass(slots=True)
class AuthenticationResult:
    """Outcome of processing an OAuth authentication request."""

    success: bool
    user_id: Optional[str]
    roles: tuple[str, ...]
    session_token: Optional[str]
    requires_two_factor: bool = False


class OAuthFlowService:
    """Coordinate OAuth authentication with user lookup and session issuance."""

    def __init__(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        *,
        two_factor_manager: TwoFactorManager | None = None,
        turnstile_verifier: TurnstileManager | None = None,
        session_ttl_seconds: int = 3600,
    ) -> None:
        self._auth_service = auth_service
        self._user_repository = user_repository
        self._session_repository = session_repository
        self._two_factor_manager = two_factor_manager
        self._turnstile_verifier = turnstile_verifier
        self._session_ttl_seconds = session_ttl_seconds

    def authenticate(self, request: OAuthRequest) -> AuthenticationResult:
        """Execute the OAuth authentication flow."""
        self._validate_state(request.state, request.expected_state)
        if self._turnstile_verifier:
            if not request.turnstile_token:
                raise ValueError("Turnstile token is required for authentication.")
            self._turnstile_verifier.verify(request.turnstile_token, request.turnstile_remote_ip)
        auth_result = self._auth_service.authenticate(provider=request.provider, code=request.code)

        user = self._user_repository.find_by_oauth_identity(request.provider, auth_result.profile.subject)
        if user is None:
            raise ValueError("User not registered for OAuth provider.")

        if self._two_factor_manager and self._two_factor_manager.is_enabled(user.user_id):
            if not request.two_factor_code:
                self._two_factor_manager.initiate_challenge(user.user_id)
                return AuthenticationResult(
                    success=False,
                    user_id=user.user_id,
                    roles=user.roles,
                    session_token=None,
                    requires_two_factor=True,
                )
            if not self._two_factor_manager.verify_code(user.user_id, request.two_factor_code):
                raise ValueError("Invalid two-factor authentication code.")

        session_record = self._issue_session(user)
        persisted = self._session_repository.create_session(session_record)
        return AuthenticationResult(
            success=True,
            user_id=user.user_id,
            roles=user.roles,
            session_token=persisted.token,
            requires_two_factor=False,
        )

    def _issue_session(self, user: UserRecord) -> SessionRecord:
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + self._session_ttl_seconds
        return SessionRecord(token=token, user_id=user.user_id, roles=user.roles, expires_at=expires_at)

    @staticmethod
    def _validate_state(state: str, expected_state: str) -> None:
        if not state or state != expected_state:
            raise ValueError("Invalid OAuth state parameter.")
