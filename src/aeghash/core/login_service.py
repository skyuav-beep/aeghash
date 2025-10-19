"""Password-based login service with audit logging, Turnstile, and 2FA support."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from aeghash.adapters.turnstile import TurnstileError
from aeghash.core.auth_flow import AuthenticationResult
from aeghash.core.auth_flow import TurnstileManager
from aeghash.core.repositories import (
    LoginAuditRecord,
    LoginAuditRepository,
    SessionRecord,
    SessionRepository,
    UserAccountRepository,
    UserRepository,
)
from aeghash.core.two_factor import TwoFactorService
from aeghash.security.passwords import verify_password


class LoginError(ValueError):
    """Raised when login credentials are invalid or the account is inactive."""


@dataclass(slots=True)
class LoginRequest:
    email: str
    password: str
    turnstile_token: Optional[str] = None
    remote_ip: Optional[str] = None
    two_factor_code: Optional[str] = None


class PasswordLoginService:
    """Authenticate locally registered users using email/password."""

    def __init__(
        self,
        account_repository: UserAccountRepository,
        identity_repository: UserRepository,
        session_repository: SessionRepository,
        audit_repository: LoginAuditRepository,
        *,
        session_ttl_seconds: int = 3600,
        email_normalizer: Callable[[str], str] | None = None,
        two_factor_service: TwoFactorService | None = None,
        turnstile_verifier: TurnstileManager | None = None,
    ) -> None:
        self._accounts = account_repository
        self._identities = identity_repository
        self._sessions = session_repository
        self._audits = audit_repository
        self._session_ttl = session_ttl_seconds
        self._normalize = email_normalizer or (lambda value: value.strip().lower())
        self._two_factor_service = two_factor_service
        self._turnstile_verifier = turnstile_verifier

    def login(self, request: LoginRequest) -> AuthenticationResult:
        normalized = self._normalize(request.email)
        if not normalized:
            raise LoginError("invalid_email")

        if self._turnstile_verifier:
            token = request.turnstile_token
            if not token:
                self._audits.log(
                    LoginAuditRecord(provider="local", status="FAILED", subject=None, reason="turnstile_missing"),
                )
                raise LoginError("turnstile_required")
            try:
                self._turnstile_verifier.verify(token, request.remote_ip)
            except TurnstileError as exc:
                self._audits.log(
                    LoginAuditRecord(provider="local", status="FAILED", subject=None, reason="turnstile_failed"),
                )
                raise LoginError("turnstile_failed") from exc

        password_value = request.password
        self._audits.log(LoginAuditRecord(provider="local", status="STARTED", subject=normalized))

        account = self._accounts.find_by_email(normalized)
        if account is None or not verify_password(password_value, account.password_hash):
            self._audits.log(
                LoginAuditRecord(provider="local", status="FAILED", subject=None, reason="invalid_credentials"),
            )
            raise LoginError("invalid_credentials")

        if not account.is_active:
            self._audits.log(
                LoginAuditRecord(provider="local", status="FAILED", subject=account.user_id, reason="inactive_account"),
            )
            raise LoginError("inactive_account")

        identity = self._identities.find_by_oauth_identity("local", normalized)
        if identity is None:
            self._audits.log(
                LoginAuditRecord(provider="local", status="FAILED", subject=account.user_id, reason="identity_missing"),
            )
            raise LoginError("identity_missing")

        if identity.two_factor_enabled:
            if not self._two_factor_service:
                self._audits.log(
                    LoginAuditRecord(
                        provider="local",
                        status="FAILED",
                        subject=account.user_id,
                        reason="two_factor_unavailable",
                    ),
                )
                raise LoginError("two_factor_unavailable")

            if not request.two_factor_code:
                self._two_factor_service.initiate_challenge(account.user_id)
                self._audits.log(
                    LoginAuditRecord(
                        provider="local",
                        status="CHALLENGE",
                        subject=account.user_id,
                        reason="two_factor_required",
                    ),
                )
                return AuthenticationResult(
                    success=False,
                    user_id=account.user_id,
                    roles=identity.roles,
                    session_token=None,
                    requires_two_factor=True,
                )

            if not self._two_factor_service.verify_code(account.user_id, request.two_factor_code):
                self._audits.log(
                    LoginAuditRecord(
                        provider="local",
                        status="FAILED",
                        subject=account.user_id,
                        reason="invalid_two_factor",
                    ),
                )
                raise LoginError("invalid_two_factor_code")

        session = self._issue_session(account.user_id, identity.roles)
        self._sessions.create_session(session)

        self._audits.log(
            LoginAuditRecord(provider="local", status="SUCCEEDED", subject=account.user_id, reason=None),
        )

        return AuthenticationResult(
            success=True,
            user_id=account.user_id,
            roles=identity.roles,
            session_token=session.token,
            requires_two_factor=False,
        )

    def _issue_session(self, user_id: str, roles: Sequence[str]) -> SessionRecord:
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + self._session_ttl
        return SessionRecord(token=token, user_id=user_id, roles=tuple(roles), expires_at=expires_at)
