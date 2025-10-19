"""Cloudflare Turnstile verification client."""

from __future__ import annotations

from typing import Any, Dict, Protocol

import httpx


class TurnstileTransport(Protocol):
    """Protocol describing the minimal transport required by TurnstileClient."""

    def post(self, url: str, data: Dict[str, Any], timeout: float | None = None) -> httpx.Response:
        ...


class TurnstileError(RuntimeError):
    """Raised when Turnstile verification fails."""


class TurnstileClient:
    """Client for verifying Cloudflare Turnstile tokens."""

    VERIFY_ENDPOINT = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    def __init__(
        self,
        *,
        secret_key: str,
        transport: TurnstileTransport | None = None,
        timeout: float = 5.0,
    ) -> None:
        if not secret_key:
            raise ValueError("Turnstile secret key must be provided.")
        self._secret_key = secret_key
        self._timeout = timeout
        self._client = transport or httpx.Client()

    def verify(self, token: str, *, remote_ip: str | None = None) -> bool:
        if not token:
            raise ValueError("Turnstile token cannot be empty.")

        payload: Dict[str, Any] = {"secret": self._secret_key, "response": token}
        if remote_ip:
            payload["remoteip"] = remote_ip

        response = self._client.post(self.VERIFY_ENDPOINT, data=payload, timeout=self._timeout)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise TurnstileError("Turnstile response is not valid JSON.") from exc

        if not isinstance(data, dict):
            raise TurnstileError("Invalid Turnstile response payload.")

        success = data.get("success")
        if success is True:
            return True

        error_codes = data.get("error-codes")
        if isinstance(error_codes, list) and error_codes:
            raise TurnstileError(f"Turnstile verification failed: {', '.join(map(str, error_codes))}")
        raise TurnstileError("Turnstile verification failed without specific error codes.")

    def close(self) -> None:
        if isinstance(self._client, httpx.Client):
            self._client.close()
