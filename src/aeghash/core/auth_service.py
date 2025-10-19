"""Authentication service orchestrating OAuth providers with logging hooks."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Mapping, Protocol

from aeghash.adapters.oauth import OAuthResult

AuthEventHook = Callable[[str, Mapping[str, object]], None]


class OAuthClient(Protocol):
    """Protocol describing the methods required from an OAuth client."""

    provider_name: str

    def authenticate(self, *, code: str) -> OAuthResult:
        ...

    def close(self) -> None:
        ...


class AuthService:
    """High-level service that delegates authentication to provider clients."""

    def __init__(
        self,
        providers: Mapping[str, OAuthClient],
        *,
        event_hook: AuthEventHook | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if not providers:
            raise ValueError("At least one OAuth provider must be supplied.")
        self._providers: Dict[str, OAuthClient] = dict(providers)
        self._event_hook = event_hook
        self._logger = logger or logging.getLogger(__name__)

    def authenticate(self, *, provider: str, code: str) -> OAuthResult:
        """Authenticate via the requested provider."""
        self._emit_event("auth.start", {"provider": provider})
        self._logger.info("OAuth authentication started", extra={"provider": provider})
        try:
            client = self._providers[provider]
        except KeyError as exc:
            self._logger.warning("OAuth provider not registered", extra={"provider": provider})
            self._emit_event("auth.error", {"provider": provider, "reason": "unknown_provider"})
            raise ValueError(f"Unknown OAuth provider: {provider}") from exc

        try:
            result = client.authenticate(code=code)
        except Exception as exc:
            self._logger.error(
                "OAuth authentication failed",
                exc_info=exc,
                extra={"provider": provider},
            )
            self._emit_event("auth.error", {"provider": provider, "reason": "exception"})
            raise

        self._emit_event(
            "auth.success",
            {"provider": provider, "subject": result.profile.subject},
        )
        self._logger.info(
            "OAuth authentication succeeded",
            extra={"provider": provider, "subject": result.profile.subject},
        )
        return result

    def close(self) -> None:
        """Close all provider clients."""
        for client in self._providers.values():
            client.close()

    def providers(self) -> Mapping[str, OAuthClient]:
        """Expose the registered providers (read-only)."""
        return dict(self._providers)

    def _emit_event(self, name: str, payload: Mapping[str, object]) -> None:
        if self._event_hook:
            self._event_hook(name, payload)
