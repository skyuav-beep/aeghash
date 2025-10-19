import json
from decimal import Decimal
from typing import Any, Dict

import httpx
import pytest

from aeghash.adapters.hashdam import (
    HashBalance,
    HashDamClient,
    HashDamHTTPTransport,
    HashDamTransport,
)


class StubHashDamTransport(HashDamTransport):
    def __init__(self, responses: Dict[str, Dict[str, Any]]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, Dict[str, Any]]] = []
        self.closed = False

    def post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((method, payload))
        return self._responses[method]

    def close(self) -> None:
        self.closed = True


def test_get_hash_balance_parses_decimal() -> None:
    transport = StubHashDamTransport(
        {
            "hashBalance": {
                "code": 0,
                "data": {"date": "2025-08-15", "credit": "651.4", "power": "8348.6"},
            },
        },
    )
    client = HashDamClient(transport)

    result = client.get_hash_balance()

    assert isinstance(result, HashBalance)
    assert result.credit == Decimal("651.4")
    assert transport.calls == [("hashBalance", {})]


def test_asset_withdraw_error_on_non_zero_code() -> None:
    transport = StubHashDamTransport(
        {
            "assetWithdrawRequest": {"code": 1, "message": "Insufficient credit"},
        },
    )
    client = HashDamClient(transport)

    with pytest.raises(ValueError):
        client.request_asset_withdrawal(coin="PEP", amount=Decimal("10"))


def test_http_transport_adds_headers_and_method(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content.decode())
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"code": 0, "data": {"date": "x", "credit": "0", "power": "0"}})

    transport = httpx.MockTransport(handler)
    client = HashDamHTTPTransport(
        base_url="https://api.pool.hashdam.com/v1",
        api_key=None,
        client=httpx.Client(transport=transport, base_url="https://api.pool.hashdam.com/v1"),
    )

    client.post("hashBalance", {})

    assert captured["json"]["method"] == "hashBalance"
    assert "X-HASHDAM-Key" not in captured["headers"]
