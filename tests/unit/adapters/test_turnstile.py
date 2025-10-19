import httpx
import pytest

from aeghash.adapters.turnstile import TurnstileClient, TurnstileError


class StubTransport:
    def __init__(self, response_json):
        self.response_json = response_json
        self.requests = []

    def post(self, url: str, data, timeout=None):
        self.requests.append((url, data))
        request = httpx.Request("POST", url)
        return httpx.Response(200, json=self.response_json, request=request)


def test_turnstile_verification_success():
    transport = StubTransport({"success": True})
    client = TurnstileClient(secret_key="secret", transport=transport)

    assert client.verify("token123", remote_ip="1.1.1.1") is True
    assert transport.requests[0][0] == TurnstileClient.VERIFY_ENDPOINT


def test_turnstile_verification_failure_with_error_code():
    transport = StubTransport({"success": False, "error-codes": ["timeout-or-duplicate"]})
    client = TurnstileClient(secret_key="secret", transport=transport)

    with pytest.raises(TurnstileError):
        client.verify("token123")


def test_turnstile_verification_invalid_payload():
    class InvalidTransport(StubTransport):
        def post(self, url: str, data, timeout=None):
            request = httpx.Request("POST", url)
            return httpx.Response(200, json=None, request=request)

    client = TurnstileClient(secret_key="secret", transport=InvalidTransport({}))

    with pytest.raises(TurnstileError):
        client.verify("token123")


def test_turnstile_empty_token_raises_value_error():
    client = TurnstileClient(secret_key="secret", transport=StubTransport({"success": True}))

    with pytest.raises(ValueError):
        client.verify("")
