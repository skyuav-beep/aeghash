import pytest

from aeghash.adapters.turnstile import TurnstileError
from aeghash.core.turnstile import TurnstileVerifier


class StubTurnstileClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, str | None]] = []

    def verify(self, token: str, remote_ip=None) -> None:
        self.calls.append((token, remote_ip))
        if self.should_fail:
            raise TurnstileError("fail")


def test_turnstile_verifier_invokes_client() -> None:
    client = StubTurnstileClient()
    verifier = TurnstileVerifier(client)

    verifier.verify("token", "1.1.1.1")

    assert client.calls == [("token", "1.1.1.1")]


def test_turnstile_verifier_propagates_errors() -> None:
    client = StubTurnstileClient(should_fail=True)
    verifier = TurnstileVerifier(client)

    with pytest.raises(TurnstileError):
        verifier.verify("token", None)
