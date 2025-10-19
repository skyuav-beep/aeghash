"""Turnstile verification helpers."""

from __future__ import annotations

from typing import Optional

from aeghash.adapters.turnstile import TurnstileClient, TurnstileError


class TurnstileVerifier:
    """Adapter that validates Turnstile tokens using the HTTP client."""

    def __init__(self, client: TurnstileClient) -> None:
        self._client = client

    def verify(self, token: str, remote_ip: Optional[str]) -> None:
        """Verify the supplied token, raising TurnstileError on failure."""
        self._client.verify(token, remote_ip=remote_ip)
