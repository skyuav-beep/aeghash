import base64
import json
from typing import Any, Dict

import pytest

from aeghash.adapters.oauth import (
    AppleOAuthClient,
    GoogleOAuthClient,
    KakaoOAuthClient,
    OAuthError,
    OAuthResult,
    OAuthTransport,
)
from aeghash.config import OAuthProviderSettings


class StubTransport(OAuthTransport):
    def __init__(self, *, post_responses: Dict[str, Dict[str, Any]], get_responses: Dict[str, Dict[str, Any]] | None = None) -> None:
        self._post = post_responses
        self._get = get_responses or {}
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        self.calls.append(("post", url))
        return dict(self._post[url])

    def get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        self.calls.append(("get", url))
        return dict(self._get[url])

    def close(self) -> None:
        self.closed = True


def make_settings() -> OAuthProviderSettings:
    return OAuthProviderSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="https://app/callback",
    )


def _make_jwt(payload: Dict[str, Any]) -> str:
    def encode(segment: Dict[str, Any]) -> str:
        raw = json.dumps(segment, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    header = encode({"alg": "none", "kid": "kid"})
    body = encode(payload)
    return f"{header}.{body}."


def test_google_oauth_returns_profile() -> None:
    transport = StubTransport(
        post_responses={
            GoogleOAuthClient.token_endpoint: {
                "access_token": "token123",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "email profile",
            },
        },
        get_responses={
            GoogleOAuthClient.profile_endpoint: {
                "sub": "user-1",
                "email": "user@example.com",
                "name": "User Example",
            },
        },
    )
    client = GoogleOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="auth-code")
    client.close()

    assert isinstance(result, OAuthResult)
    assert result.token.access_token == "token123"
    assert result.profile.provider == "google"
    assert result.profile.subject == "user-1"
    assert transport.closed


def test_kakao_oauth_parses_profile_fields() -> None:
    transport = StubTransport(
        post_responses={
            KakaoOAuthClient.token_endpoint: {
                "access_token": "token456",
                "token_type": "bearer",
            },
        },
        get_responses={
            KakaoOAuthClient.profile_endpoint: {
                "id": 987654321,
                "kakao_account": {
                    "email": "kakao@example.com",
                    "profile": {"nickname": "kakao-user"},
                },
            },
        },
    )
    client = KakaoOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="auth-code")

    assert result.profile.provider == "kakao"
    assert result.profile.subject == "987654321"
    assert result.profile.email == "kakao@example.com"
    assert result.profile.name == "kakao-user"


def test_apple_oauth_uses_id_token_payload() -> None:
    id_token = _make_jwt({"sub": "apple-user", "email": "apple@example.com", "name": "Apple User"})
    transport = StubTransport(
        post_responses={
            AppleOAuthClient.token_endpoint: {
                "access_token": "token789",
                "id_token": id_token,
                "token_type": "Bearer",
            },
        },
    )
    client = AppleOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="auth-code")

    assert result.profile.subject == "apple-user"
    assert result.profile.email == "apple@example.com"
    assert result.profile.provider == "apple"


def test_token_exchange_error_raises_oauth_error() -> None:
    transport = StubTransport(
        post_responses={
            GoogleOAuthClient.token_endpoint: {
                "error": "invalid_grant",
                "error_description": "Invalid code",
            },
        },
    )
    client = GoogleOAuthClient(transport=transport, settings=make_settings())

    with pytest.raises(OAuthError):
        client.authenticate(code="bad-code")


def test_missing_profile_endpoint_raises_error() -> None:
    class DummyClient(GoogleOAuthClient):
        profile_endpoint = None

    transport = StubTransport(
        post_responses={
            GoogleOAuthClient.token_endpoint: {
                "access_token": "token123",
            },
        },
    )
    client = DummyClient(transport=transport, settings=make_settings())

    with pytest.raises(OAuthError):
        client.authenticate(code="auth-code")
