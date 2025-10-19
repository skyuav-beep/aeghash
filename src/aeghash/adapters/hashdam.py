"""HashDam API client and response models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Protocol

import httpx


class HashDamTransport(Protocol):
    """Protocol describing the minimal transport required by HashDamClient."""

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def close(self) -> None:  # pragma: no cover - interface only
        ...


@dataclass(slots=True)
class HashBalance:
    """Hash balance summary."""

    date: str
    credit: Decimal
    power: Decimal


@dataclass(slots=True)
class AssetWithdrawal:
    """HashDam asset withdrawal request result."""

    withdraw_id: str
    coin: str
    amount: Decimal


class HashDamClient:
    """High-level client for HashDam operations."""

    def __init__(self, transport: HashDamTransport) -> None:
        self._transport = transport

    def get_hash_balance(self) -> HashBalance:
        """Retrieve current hash balance."""
        response = self._transport.post("hashBalance", {})
        data = _validate_hashdam_response(response)
        return HashBalance(
            date=data["date"],
            credit=Decimal(data["credit"]),
            power=Decimal(data["power"]),
        )

    def request_asset_withdrawal(self, *, coin: str, amount: Decimal) -> AssetWithdrawal:
        """Request withdrawal for a mined asset."""
        response = self._transport.post(
            "assetWithdrawRequest",
            {
                "coin": coin,
                "amount": str(amount),
            },
        )
        data = _validate_hashdam_response(response)
        return AssetWithdrawal(
            withdraw_id=data["withdrawId"],
            coin=data["coin"],
            amount=Decimal(data["amount"]),
        )

    def close(self) -> None:
        """Close underlying transport."""
        self._transport.close()


class HashDamHTTPTransport:
    """HTTPX-based transport for HashDam API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)
        self._api_key = api_key

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = {"method": method, **payload}
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-HASHDAM-Key"] = self._api_key

        response = self._client.post("", json=body, headers=headers)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


def _validate_hashdam_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate common HashDam response envelope."""
    code = response.get("code")
    if code not in (0, None):
        message = response.get("message", "Unknown error")
        raise ValueError(f"HashDam API error: {message}")

    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("HashDam API response missing 'data' object.")
    return data
