from decimal import Decimal

import httpx
import pytest

from aeghash.adapters.mblock import MBlockClient, MBlockHTTPTransport
from aeghash.config import MBlockSettings
from aeghash.core.wallet_service import WalletService
from aeghash.utils import InMemoryWalletRepository


def test_wallet_flow_with_inmemory_repo(monkeypatch):
    """Integration-style test using in-memory repository and mocked transport."""
    captured_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode())
        captured_requests.append(payload)
        method = payload["method"]
        if method == "requestWallet":
            return httpx.Response(
                200,
                json={"result": True, "address": "0xabc", "walletKey": "wallet_key"},
            )
        if method == "balanceOf":
            return httpx.Response(200, json={"result": True, "amount": "5"})
        if method == "transferByWalletKey":
            return httpx.Response(200, json={"result": True, "txid": "tx123"})
        return httpx.Response(200, json={"result": True, "token": "token123"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://agent.mblockapi.com/bsc")

    transport_layer = MBlockHTTPTransport(
        base_url="https://agent.mblockapi.com/bsc",
        api_key="test-key",
        client=http_client,
    )
    client = MBlockClient(transport_layer)
    settings = MBlockSettings(
        base_url="https://agent.mblockapi.com/bsc",
        api_key="test-key",
        transit_fee=0.0002,
        transit_fee_wallet_key="fee_wallet",
        transit_callback_url="https://callback",
    )
    repository = InMemoryWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    wallet_info = service.create_wallet(user_id="user-1")
    balance = service.get_balance(address=wallet_info.address)
    receipt = service.transfer_token(
        wallet_id="wallet-1",
        wallet_key=wallet_info.wallet_key,
        to="0xreceiver",
        amount=Decimal("1.0"),
    )

    assert wallet_info.wallet_key == "wallet_key"
    assert balance == Decimal("5")
    assert receipt.txid == "tx123"
    assert repository.wallets[0].user_id == "user-1"
    assert repository.transactions[0].status == "submitted"


def test_wallet_transfer_failure_logs_failure():
    captured_requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode())
        captured_requests.append(payload)
        method = payload["method"]
        if method == "requestWallet":
            return httpx.Response(
                200,
                json={"result": True, "address": "0xabc", "walletKey": "wallet_key"},
            )
        if method == "transferByWalletKey":
            return httpx.Response(200, json={"result": False, "message": "Insufficient"})
        return httpx.Response(200, json={"result": True, "amount": "5"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://agent.mblockapi.com/bsc")
    transport_layer = MBlockHTTPTransport(
        base_url="https://agent.mblockapi.com/bsc",
        api_key="test-key",
        client=http_client,
    )
    client = MBlockClient(transport_layer)
    settings = MBlockSettings(
        base_url="https://agent.mblockapi.com/bsc",
        api_key="test-key",
    )
    repository = InMemoryWalletRepository()
    service = WalletService(client=client, settings=settings, repository=repository)

    wallet_info = service.create_wallet(user_id="user-1")
    with pytest.raises(ValueError):
        service.transfer_token(
            wallet_id="wallet-1",
            wallet_key=wallet_info.wallet_key,
            to="0xreceiver",
            amount=Decimal("1.0"),
        )

    assert repository.transactions[0].status == "failed"
    assert repository.transactions[0].txid is None
