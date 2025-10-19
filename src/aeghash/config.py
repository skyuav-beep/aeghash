"""Configuration utilities for environment-driven settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

DEFAULT_HASHDAM_BASE_URL = "https://api.pool.hashdam.com/v1"
DEV_MODE_ENV = "AEGHASH_DEV_MODE"

DEV_DEFAULTS = {
    "MBLOCK_API_BASE_URL": "https://sandbox.mblock.local",
    "MBLOCK_API_KEY": "dev-mblock-api-key",
    "MBLOCK_TRANSIT_FEE": "0",
    "DATABASE_URL": "sqlite+pysqlite:///./aeghash-dev.sqlite3",
    "SECRET_KEY": "dev-secret-key",
    "TURNSTILE_SECRET_KEY": "dev-turnstile-secret",
    "GOOGLE_OAUTH_CLIENT_ID": "dev-google-client",
    "GOOGLE_OAUTH_CLIENT_SECRET": "dev-google-secret",
    "GOOGLE_OAUTH_REDIRECT_URI": "https://localhost/auth/google",
    "KAKAO_OAUTH_CLIENT_ID": "dev-kakao-client",
    "KAKAO_OAUTH_CLIENT_SECRET": "dev-kakao-secret",
    "KAKAO_OAUTH_REDIRECT_URI": "https://localhost/auth/kakao",
    "APPLE_OAUTH_CLIENT_ID": "dev-apple-client",
    "APPLE_OAUTH_CLIENT_SECRET": "dev-apple-secret",
    "APPLE_OAUTH_REDIRECT_URI": "https://localhost/auth/apple",
}


@dataclass
class HashDamSettings:
    base_url: str = DEFAULT_HASHDAM_BASE_URL
    api_key: Optional[str] = None


@dataclass
class MBlockSettings:
    base_url: str
    api_key: str
    transit_fee: Optional[float] = None
    transit_fee_wallet_key: Optional[str] = None
    transit_callback_url: Optional[str] = None


@dataclass
class OAuthProviderSettings:
    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass
class OAuthSettings:
    google: OAuthProviderSettings
    kakao: OAuthProviderSettings
    apple: OAuthProviderSettings


@dataclass
class TurnstileSettings:
    secret_key: str


@dataclass
class AppSettings:
    hashdam: HashDamSettings
    mblock: MBlockSettings
    oauth: OAuthSettings
    turnstile: TurnstileSettings
    database_url: str
    secret_key: str
    kpi_alerts: Optional["KpiAlertSettings"] = None


@dataclass
class KpiAlertSettings:
    personal_volume_floor: Optional[Decimal] = None
    group_volume_floor: Optional[Decimal] = None


def load_settings() -> AppSettings:
    """Load settings from environment variables."""
    mblock = MBlockSettings(
        base_url=_require_env("MBLOCK_API_BASE_URL"),
        api_key=_require_env("MBLOCK_API_KEY"),
        transit_fee=_optional_float("MBLOCK_TRANSIT_FEE"),
        transit_fee_wallet_key=os.environ.get("MBLOCK_TRANSIT_FEE_WALLET_KEY"),
        transit_callback_url=os.environ.get("MBLOCK_TRANSIT_CALLBACK_URL"),
    )

    hashdam = HashDamSettings(
        base_url=os.environ.get("HASHDAM_API_BASE_URL", DEFAULT_HASHDAM_BASE_URL),
        api_key=os.environ.get("HASHDAM_API_KEY"),
    )

    database_url = os.environ.get("DATABASE_URL")
    secret_key = os.environ.get("SECRET_KEY")
    if is_dev_mode():
        if not database_url:
            database_url = DEV_DEFAULTS["DATABASE_URL"]
        if not secret_key:
            secret_key = DEV_DEFAULTS["SECRET_KEY"]

    if not database_url or not secret_key:
        raise RuntimeError("DATABASE_URL and SECRET_KEY must be defined.")

    return AppSettings(
        hashdam=hashdam,
        mblock=mblock,
        oauth=_load_oauth_settings(),
        turnstile=_load_turnstile_settings(),
        database_url=database_url,
        secret_key=secret_key,
        kpi_alerts=_load_kpi_alert_settings(),
    )


def _optional_float(var_name: str) -> Optional[float]:
    """Convert optional environment variable to float."""
    value = os.environ.get(var_name)
    if (value is None or value == "") and is_dev_mode():
        value = DEV_DEFAULTS.get(var_name)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Environment variable {var_name} must be a float.") from exc


def _load_oauth_settings() -> OAuthSettings:
    """Load OAuth provider settings."""

    return OAuthSettings(
        google=OAuthProviderSettings(
            client_id=_require_env("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=_require_env("GOOGLE_OAUTH_CLIENT_SECRET"),
            redirect_uri=_require_env("GOOGLE_OAUTH_REDIRECT_URI"),
        ),
        kakao=OAuthProviderSettings(
            client_id=_require_env("KAKAO_OAUTH_CLIENT_ID"),
            client_secret=_require_env("KAKAO_OAUTH_CLIENT_SECRET"),
            redirect_uri=_require_env("KAKAO_OAUTH_REDIRECT_URI"),
        ),
        apple=OAuthProviderSettings(
            client_id=_require_env("APPLE_OAUTH_CLIENT_ID"),
            client_secret=_require_env("APPLE_OAUTH_CLIENT_SECRET"),
            redirect_uri=_require_env("APPLE_OAUTH_REDIRECT_URI"),
        ),
    )


def _require_env(var_name: str) -> str:
    """Fetch a required environment variable."""
    value = os.environ.get(var_name)
    if not value:
        if is_dev_mode():
            default = DEV_DEFAULTS.get(var_name)
            if default:
                return default
        raise RuntimeError(f"{var_name} must be defined.")
    return value


def _load_turnstile_settings() -> TurnstileSettings:
    return TurnstileSettings(secret_key=_require_env("TURNSTILE_SECRET_KEY"))


def _optional_decimal(var_name: str) -> Optional[Decimal]:
    value = os.environ.get(var_name)
    if value in ("", None):
        return None
    try:
        return Decimal(value)
    except (ArithmeticError, ValueError) as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Environment variable {var_name} must be a decimal value.") from exc


def _load_kpi_alert_settings() -> Optional[KpiAlertSettings]:
    personal = _optional_decimal("KPI_ALERT_PERSONAL_VOLUME_FLOOR")
    group = _optional_decimal("KPI_ALERT_GROUP_VOLUME_FLOOR")
    if personal is None and group is None:
        return None
    return KpiAlertSettings(personal_volume_floor=personal, group_volume_floor=group)


def is_dev_mode() -> bool:
    """Return True when development mode is enabled via environment."""
    value = os.environ.get(DEV_MODE_ENV, "")
    return value.lower() in {"1", "true", "yes", "on"}
