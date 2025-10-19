import pytest

from aeghash.adapters.oauth import OAuthProfile, OAuthResult, OAuthToken
from aeghash.core.auth_service import AuthService, OAuthClient


class StubOAuthClient(OAuthClient):
    provider_name = "google"

    def __init__(self, *, result: OAuthResult) -> None:
        self._result = result
        self.calls: list[str] = []
        self.closed = False

    def authenticate(self, *, code: str) -> OAuthResult:
        self.calls.append(code)
        return self._result

    def close(self) -> None:
        self.closed = True


def make_result(provider: str = "google") -> OAuthResult:
    return OAuthResult(
        token=OAuthToken(
            access_token="access",
            token_type="Bearer",
            expires_in=3600,
            refresh_token=None,
            id_token=None,
            scope=None,
            raw={},
        ),
        profile=OAuthProfile(
            provider=provider,
            subject="user",
            email="user@example.com",
            name="User",
            raw={},
        ),
    )


def test_auth_service_dispatches_to_provider() -> None:
    stub = StubOAuthClient(result=make_result())
    service = AuthService({"google": stub})

    result = service.authenticate(provider="google", code="auth-code")

    assert result.profile.subject == "user"
    assert stub.calls == ["auth-code"]


def test_auth_service_unknown_provider_raises() -> None:
    events: list[tuple[str, dict[str, object]]] = []

    def hook(name: str, payload):
        events.append((name, dict(payload)))

    service = AuthService({"google": StubOAuthClient(result=make_result())}, event_hook=hook)

    with pytest.raises(ValueError):
        service.authenticate(provider="unknown", code="code")

    assert ("auth.start", {"provider": "unknown"}) in events
    assert ("auth.error", {"provider": "unknown", "reason": "unknown_provider"}) in events


def test_auth_service_close_closes_all_providers() -> None:
    google_stub = StubOAuthClient(result=make_result("google"))
    kakao_stub = StubOAuthClient(result=make_result("kakao"))
    kakao_stub.provider_name = "kakao"
    service = AuthService({"google": google_stub, "kakao": kakao_stub})

    service.close()

    assert google_stub.closed
    assert kakao_stub.closed


def test_auth_service_requires_providers() -> None:
    with pytest.raises(ValueError):
        AuthService({})


def test_auth_service_emits_events_on_success() -> None:
    stub = StubOAuthClient(result=make_result())
    events: list[tuple[str, dict[str, object]]] = []

    def hook(name: str, payload):
        events.append((name, dict(payload)))

    service = AuthService({"google": stub}, event_hook=hook)
    service.authenticate(provider="google", code="auth-code")

    assert events[0][0] == "auth.start"
    assert events[-1] == ("auth.success", {"provider": "google", "subject": "user"})


def test_auth_service_emits_error_on_client_failure() -> None:
    class FailingClient(StubOAuthClient):
        def authenticate(self, *, code: str) -> OAuthResult:
            raise RuntimeError("boom")

    failing = FailingClient(result=make_result())
    events: list[tuple[str, dict[str, object]]] = []

    def hook(name: str, payload):
        events.append((name, dict(payload)))

    service = AuthService({"google": failing}, event_hook=hook)

    with pytest.raises(RuntimeError):
        service.authenticate(provider="google", code="auth-code")

    assert events[-1] == ("auth.error", {"provider": "google", "reason": "exception"})
