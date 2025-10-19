"""Development-mode OAuth transport returning static provider responses."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping

from aeghash.adapters.oauth import OAuthTransport


@dataclass(frozen=True)
class DevOAuthProfile:
    """Static OAuth profile used for development mode stubs."""

    subject: str
    email: str | None
    name: str | None


DEV_OAUTH_PROFILES: Mapping[str, DevOAuthProfile] = {
    "google": DevOAuthProfile("dev-google-user", "dev.google@example.com", "Dev Google"),
    "kakao": DevOAuthProfile("10001", "dev.kakao@example.com", "Dev Kakao"),
    "apple": DevOAuthProfile("dev-apple-user", "dev.apple@example.com", "Dev Apple"),
}


class DevOAuthTransport(OAuthTransport):
    """Stub transport that mimics OAuth provider responses for development mode."""

    def __init__(self, provider: str, profiles: Mapping[str, DevOAuthProfile] | None = None) -> None:
        self._provider = provider
        self._profiles: Mapping[str, DevOAuthProfile] = profiles or DEV_OAUTH_PROFILES

    def post(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        profile = self._profile()
        response: Dict[str, Any] = {
            "access_token": f"{self._provider}-dev-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "profile email",
        }
        if self._provider == "apple":
            response["id_token"] = _encode_id_token(profile)
        return response

    def get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        profile = self._profile()
        if self._provider == "google":
            return {
                "sub": profile.subject,
                "email": profile.email,
                "name": profile.name,
            }
        if self._provider == "kakao":
            kakao_id: Any = profile.subject
            if isinstance(kakao_id, str) and kakao_id.isdigit():
                kakao_id = int(kakao_id)
            return {
                "id": kakao_id,
                "kakao_account": {
                    "email": profile.email,
                    "profile": {
                        "nickname": profile.name or str(kakao_id),
                    },
                },
            }
        raise RuntimeError(f"Provider '{self._provider}' does not expose a profile endpoint in development mode.")

    def close(self) -> None:
        # No underlying resources to release.
        return None

    def _profile(self) -> DevOAuthProfile:
        try:
            return self._profiles[self._provider]
        except KeyError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Development profile missing for provider '{self._provider}'.") from exc


def _encode_id_token(profile: DevOAuthProfile) -> str:
    header = {"alg": "none", "kid": "dev"}
    payload = {"sub": profile.subject, "email": profile.email, "name": profile.name}
    return ".".join((_b64encode(header), _b64encode(payload), ""))


def _b64encode(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
