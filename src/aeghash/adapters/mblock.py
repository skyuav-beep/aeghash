"""MBlock API client and response models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional, Protocol

import httpx


class MBlockTransport(Protocol):
    """Protocol describing minimal transport requirements."""

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def close(self) -> None:  # pragma: no cover - interface definition
        ...


@dataclass(slots=True)
class WalletInfo:
    """Wallet creation response."""

    address: str
    wallet_key: str


@dataclass(slots=True)
class TransferReceipt:
    """Token transfer receipt."""

    txid: str
    message: Optional[str]


@dataclass(slots=True)
class TransitToken:
    """Transit request token."""

    token: str
    message: Optional[str]


class MBlockClient:
    """High-level client for MBlock wallet operations."""

    def __init__(self, transport: MBlockTransport) -> None:
        self._transport = transport

    def get_balance(self, *, address: str, contract: Optional[str] = None) -> Decimal:
        """Return token or native balance as Decimal."""
        payload: Dict[str, Any] = {"address": address}
        if contract:
            payload["contract"] = contract

        response = self._transport.post("balanceOf", payload)
        data = _validate_result(response)
        amount = data.get("amount", "0")
        return Decimal(str(amount))

    def request_wallet(self) -> WalletInfo:
        """Create a new wallet key."""
        response = self._transport.post("requestWallet", {})
        data = _validate_result(response)
        return WalletInfo(address=data["address"], wallet_key=data["walletKey"])

    def transfer_by_wallet_key(
        self,
        *,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: Optional[str] = None,
    ) -> TransferReceipt:
        """Transfer token using wallet key."""
        payload: Dict[str, Any] = {
            "walletKey": wallet_key,
            "to": to,
            "amount": str(amount),
        }
        if contract:
            payload["contract"] = contract

        response = self._transport.post("transferByWalletKey", payload)
        data = _validate_result(response)
        return TransferReceipt(txid=data["txid"], message=data.get("message"))

    def transit_by_wallet_key(
        self,
        *,
        wallet_key: str,
        to: str,
        amount: Decimal,
        contract: str,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> TransitToken:
        """Request transit transfer (async)."""
        payload: Dict[str, Any] = {
            "walletKey": wallet_key,
            "to": to,
            "amount": str(amount),
            "contract": contract,
        }
        if config_override:
            payload["config"] = config_override

        response = self._transport.post("transitByWalletKey", payload)
        data = _validate_result(response)
        return TransitToken(token=data["token"], message=data.get("message"))

    def close(self) -> None:
        self._transport.close()


class MBlockHTTPTransport:
    """HTTPX transport for MBlock API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)
        self._api_key = api_key

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = {"method": method, **payload}
        headers = {
            "Content-Type": "application/json",
            "X-MBLOCK-Key": self._api_key,
        }
        response = self._client.post("", json=body, headers=headers)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


def _validate_result(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate MBlock response envelope."""
    if not response.get("result", False):
        message = response.get("message", "Unknown error")
        raise ValueError(f"MBlock API error: {message}")

    data = {k: v for k, v in response.items() if k not in {"result"}}
    return data
