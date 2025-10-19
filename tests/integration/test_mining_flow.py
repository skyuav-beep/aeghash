from decimal import Decimal

import httpx
import pytest

from aeghash.adapters.hashdam import HashDamClient, HashDamHTTPTransport
from aeghash.core.mining_service import MiningService
from aeghash.utils import InMemoryMiningRepository


def test_mining_flow_with_inmemory_repo():
    """Integration-style test using in-memory mining repository with mocked transport."""
    captured_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode())
        captured_requests.append(payload)
        if payload["method"] == "hashBalance":
            return httpx.Response(
                200,
                json={"code": 0, "data": {"date": "2025-08-15", "credit": "10", "power": "100"}},
            )
        if payload["method"] == "assetWithdrawRequest":
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "data": {
                        "withdrawId": "wd123",
                        "coin": payload["coin"],
                        "amount": payload["amount"],
                    },
                },
            )
        raise AssertionError("Unexpected method")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.pool.hashdam.com/v1")

    transport_layer = HashDamHTTPTransport(
        base_url="https://api.pool.hashdam.com/v1",
        api_key=None,
        client=http_client,
    )
    client = HashDamClient(transport_layer)
    repository = InMemoryMiningRepository()
    service = MiningService(client, repository)

    balance = service.get_balance(user_id="user-1")
    withdrawal = service.request_withdrawal(user_id="user-1", coin="PEP", amount=Decimal("5"))

    assert balance.credit == Decimal("10")
    assert repository.balances[0].user_id == "user-1"
    assert withdrawal.withdraw_id == "wd123"
    assert repository.withdrawals[0].amount == Decimal("5")
    assert repository.withdrawals[0].status == "submitted"


def test_mining_withdrawal_failure_logs_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode())
        if payload["method"] == "assetWithdrawRequest":
            return httpx.Response(200, json={"code": 1, "message": "Insufficient"})
        return httpx.Response(
            200,
            json={"code": 0, "data": {"date": "2025-08-15", "credit": "10", "power": "100"}},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.pool.hashdam.com/v1")
    transport_layer = HashDamHTTPTransport(
        base_url="https://api.pool.hashdam.com/v1",
        api_key=None,
        client=http_client,
    )
    client = HashDamClient(transport_layer)
    repository = InMemoryMiningRepository()
    service = MiningService(client, repository)

    with pytest.raises(ValueError):
        service.request_withdrawal(user_id="user-1", coin="PEP", amount=Decimal("5"))

    assert repository.withdrawals[0].status == "failed"
