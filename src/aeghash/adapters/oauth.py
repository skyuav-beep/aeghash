"""OAuth provider clients for Google, Kakao, and Apple."""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Protocol

import httpx

from aeghash.config import OAuthProviderSettings


class OAuthError(RuntimeError):
    """Raised when OAuth exchange fails."""


class OAuthTransport(Protocol):
    """Protocol describing the minimal transport required by OAuth clients."""

    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        ...

    def get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        ...

    def close(self) -> None:  # pragma: no cover - interface only
        ...


@dataclass(slots=True)
class OAuthToken:
    """Token exchange result."""

    access_token: str
    token_type: str
    expires_in: int | None
    refresh_token: str | None
    id_token: str | None
    scope: str | None
    raw: Mapping[str, Any]


@dataclass(slots=True)
class OAuthProfile:
    """Basic user profile resolved from a provider."""

    provider: str
    subject: str
    email: str | None
    name: str | None
    raw: Mapping[str, Any]


@dataclass(slots=True)
class OAuthResult:
    """Combined result of an OAuth authorization code exchange."""

    token: OAuthToken
    profile: OAuthProfile


class OAuthHTTPTransport:
    """HTTPX-based transport for OAuth providers."""

    def __init__(self, *, client: httpx.Client | None = None, timeout: float = 10.0) -> None:
        self._client = client or httpx.Client(timeout=timeout)

    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        response = self._client.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        response = self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


class BaseOAuthClient:
    """Shared logic for provider-specific OAuth clients."""

    provider_name: str
    token_endpoint: str
    profile_endpoint: str | None = None

    def __init__(self, *, transport: OAuthTransport, settings: OAuthProviderSettings) -> None:
        self._transport = transport
        self._settings = settings

    def authenticate(self, *, code: str) -> OAuthResult:
        """Exchange an authorization code and resolve the user profile."""
        token = self._exchange_code(code=code)
        profile = self._fetch_profile(token=token)
        return OAuthResult(token=token, profile=profile)

    def close(self) -> None:
        """Close the underlying transport."""
        self._transport.close()

    def _exchange_code(self, *, code: str) -> OAuthToken:
        payload = {
            "code": code,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
            "redirect_uri": self._settings.redirect_uri,
            "grant_type": "authorization_code",
        }
        payload.update(self._token_payload(code=code))

        data = self._transport.post(
            self.token_endpoint,
            data=payload,
            headers=self._token_headers(),
        )
        return self._parse_token_response(data)

    def _token_payload(self, *, code: str) -> Dict[str, Any]:
        return {}

    def _token_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/x-www-form-urlencoded"}

    def _parse_token_response(self, data: Dict[str, Any]) -> OAuthToken:
        if "error" in data:
            description = data.get("error_description") or data["error"]
            raise OAuthError(f"{self.provider_name} token exchange failed: {description}")

        access_token = data.get("access_token")
        if not isinstance(access_token, str):
            raise OAuthError(f"{self.provider_name} response missing access_token.")

        expires_in_value = data.get("expires_in")
        expires_in = int(expires_in_value) if isinstance(expires_in_value, (int, str)) else None

        return OAuthToken(
            access_token=access_token,
            token_type=str(data.get("token_type", "Bearer")),
            expires_in=expires_in,
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            scope=data.get("scope"),
            raw=data,
        )

    def _fetch_profile(self, *, token: OAuthToken) -> OAuthProfile:
        if not self.profile_endpoint:
            raise OAuthError(f"{self.provider_name} does not expose a profile endpoint.")

        data = self._transport.get(
            self.profile_endpoint,
            headers={"Authorization": f"Bearer {token.access_token}"},
        )
        return self._parse_profile(data=data, token=token)

    def _parse_profile(self, *, data: Dict[str, Any], token: OAuthToken) -> OAuthProfile:
        raise NotImplementedError


class GoogleOAuthClient(BaseOAuthClient):
    """Google OAuth implementation."""

    provider_name = "google"
    token_endpoint = "https://oauth2.googleapis.com/token"
    profile_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"

    def _parse_profile(self, *, data: Dict[str, Any], token: OAuthToken) -> OAuthProfile:
        subject = _require_str(data, "sub", provider=self.provider_name)
        email = data.get("email")
        name = data.get("name") or data.get("given_name")
        return OAuthProfile(
            provider=self.provider_name,
            subject=subject,
            email=email if isinstance(email, str) else None,
            name=name if isinstance(name, str) else None,
            raw=data,
        )


class KakaoOAuthClient(BaseOAuthClient):
    """Kakao OAuth implementation."""

    provider_name = "kakao"
    token_endpoint = "https://kauth.kakao.com/oauth/token"
    profile_endpoint = "https://kapi.kakao.com/v2/user/me"

    def _parse_profile(self, *, data: Dict[str, Any], token: OAuthToken) -> OAuthProfile:
        subject_value = data.get("id")
        if not isinstance(subject_value, (str, int)):
            raise OAuthError("kakao response missing user id.")

        account = data.get("kakao_account") if isinstance(data.get("kakao_account"), dict) else {}
        email = account.get("email") if isinstance(account.get("email"), str) else None
        profile = account.get("profile") if isinstance(account.get("profile"), dict) else {}
        nickname = profile.get("nickname") if isinstance(profile.get("nickname"), str) else None

        return OAuthProfile(
            provider=self.provider_name,
            subject=str(subject_value),
            email=email,
            name=nickname,
            raw=data,
        )


class AppleOAuthClient(BaseOAuthClient):
    """Apple OAuth implementation using ID token parsing for profile data."""

    provider_name = "apple"
    token_endpoint = "https://appleid.apple.com/auth/token"
    profile_endpoint = None

    def _fetch_profile(self, *, token: OAuthToken) -> OAuthProfile:
        if not token.id_token:
            raise OAuthError("apple response missing id_token.")
        payload = _decode_jwt_payload(token.id_token, provider=self.provider_name)

        subject = _require_str(payload, "sub", provider=self.provider_name)
        email_value = payload.get("email")
        name_value = payload.get("name")

        return OAuthProfile(
            provider=self.provider_name,
            subject=subject,
            email=email_value if isinstance(email_value, str) else None,
            name=name_value if isinstance(name_value, str) else None,
            raw=payload,
        )


def _require_str(data: Mapping[str, Any], key: str, *, provider: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise OAuthError(f"{provider} response missing {key}.")
    return value


def _decode_jwt_payload(token: str, *, provider: str) -> Dict[str, Any]:
    """Decode a JWT payload without signature verification."""
    try:
        _header, payload, _signature = token.split(".")
    except ValueError as exc:
        raise OAuthError(f"{provider} id_token is not a valid JWT.") from exc

    padded_payload = payload + "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded_payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except (binascii.Error, json.JSONDecodeError) as exc:
        raise OAuthError(f"{provider} id_token payload could not be decoded.") from exc
