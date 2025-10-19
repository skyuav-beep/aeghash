import json
from decimal import Decimal
from typing import Any, Dict

import httpx
import pytest

from aeghash.adapters.mblock import MBlockClient, MBlockHTTPTransport, MBlockTransport, TransitToken, WalletInfo


class StubMBlockTransport(MBlockTransport):
    def __init__(self, responses: Dict[str, Dict[str, Any]]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, Dict[str, Any]]] = []
        self.closed = False

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((method, payload))
        return self._responses[method]

    def close(self) -> None:
        self.closed = True


def test_request_wallet_success() -> None:
    transport = StubMBlockTransport(
        {
            "requestWallet": {
                "result": True,
                "address": "0x123",
                "walletKey": "wallet",
            },
        },
    )
    client = MBlockClient(transport)

    info = client.request_wallet()

    assert isinstance(info, WalletInfo)
    assert info.wallet_key == "wallet"
    assert transport.calls == [("requestWallet", {})]


def test_transfer_by_wallet_key_error() -> None:
    transport = StubMBlockTransport(
        {
            "transferByWalletKey": {"result": False, "message": "Insufficient funds"},
        },
    )
    client = MBlockClient(transport)

    with pytest.raises(ValueError):
        client.transfer_by_wallet_key(
            wallet_key="wallet",
            to="0xabc",
            amount=Decimal("1"),
        )


def test_transit_request_returns_token() -> None:
    transport = StubMBlockTransport(
        {
            "transitByWalletKey": {"result": True, "token": "token123"},
        },
    )
    client = MBlockClient(transport)

    result = client.transit_by_wallet_key(
        wallet_key="wallet",
        to="0xabc",
        contract="0xcontract",
        amount=Decimal("0.05"),
    )

    assert isinstance(result, TransitToken)
    assert result.token == "token123"
    assert transport.calls[0][1]["contract"] == "0xcontract"


def test_http_transport_injects_api_key() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content.decode())
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"result": True, "amount": "1.0"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://mock.mblock")
    mblock_transport = MBlockHTTPTransport(
        base_url="https://mock.mblock",
        api_key="secret",
        client=http_client,
    )

    mblock_transport.post("balanceOf", {"address": "0xabc"})

    assert captured["json"]["method"] == "balanceOf"
    assert captured["headers"].get("X-MBLOCK-Key") == "secret" or captured["headers"].get("x-mblock-key") == "secret"
