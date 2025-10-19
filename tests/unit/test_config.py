import os
from contextlib import contextmanager
from typing import Iterator

import pytest

from aeghash.config import DEV_DEFAULTS, AppSettings, load_settings


@contextmanager
def env_override(env: dict[str, str], *, clear: tuple[str, ...] = ()) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in set(env) | set(clear)}
    try:
        for key in clear:
            os.environ.pop(key, None)
        os.environ.update(env)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_load_settings_success() -> None:
    with env_override(
        {
            "MBLOCK_API_BASE_URL": "https://mock.mblock",
            "MBLOCK_API_KEY": "secret",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "SECRET_KEY": "super-secret",
            "TURNSTILE_SECRET_KEY": "turnstile-secret",
            "GOOGLE_OAUTH_CLIENT_ID": "google-id",
            "GOOGLE_OAUTH_CLIENT_SECRET": "google-secret",
            "GOOGLE_OAUTH_REDIRECT_URI": "https://app/callback/google",
            "KAKAO_OAUTH_CLIENT_ID": "kakao-id",
            "KAKAO_OAUTH_CLIENT_SECRET": "kakao-secret",
            "KAKAO_OAUTH_REDIRECT_URI": "https://app/callback/kakao",
            "APPLE_OAUTH_CLIENT_ID": "apple-id",
            "APPLE_OAUTH_CLIENT_SECRET": "apple-secret",
            "APPLE_OAUTH_REDIRECT_URI": "https://app/callback/apple",
        },
    ):
        settings = load_settings()

    assert isinstance(settings, AppSettings)
    assert settings.mblock.base_url == "https://mock.mblock"
    assert settings.hashdam.base_url.endswith("/v1")
    assert settings.oauth.google.client_id == "google-id"


def test_load_settings_fail_when_missing_mblock_config() -> None:
    with env_override(
        {
            "GOOGLE_OAUTH_CLIENT_ID": "google-id",
            "GOOGLE_OAUTH_CLIENT_SECRET": "google-secret",
            "GOOGLE_OAUTH_REDIRECT_URI": "https://app/callback/google",
            "KAKAO_OAUTH_CLIENT_ID": "kakao-id",
            "KAKAO_OAUTH_CLIENT_SECRET": "kakao-secret",
            "KAKAO_OAUTH_REDIRECT_URI": "https://app/callback/kakao",
            "APPLE_OAUTH_CLIENT_ID": "apple-id",
            "APPLE_OAUTH_CLIENT_SECRET": "apple-secret",
            "APPLE_OAUTH_REDIRECT_URI": "https://app/callback/apple",
            "TURNSTILE_SECRET_KEY": "turnstile-secret",
        },
        clear=(
            "MBLOCK_API_BASE_URL",
            "MBLOCK_API_KEY",
            "DATABASE_URL",
            "SECRET_KEY",
        ),
    ):
        with pytest.raises(RuntimeError):
            load_settings()


def test_optional_float_validation() -> None:
    with env_override(
        {
            "MBLOCK_API_BASE_URL": "https://mock.mblock",
            "MBLOCK_API_KEY": "secret",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "SECRET_KEY": "super-secret",
            "MBLOCK_TRANSIT_FEE": "invalid",
            "TURNSTILE_SECRET_KEY": "turnstile-secret",
            "GOOGLE_OAUTH_CLIENT_ID": "google-id",
            "GOOGLE_OAUTH_CLIENT_SECRET": "google-secret",
            "GOOGLE_OAUTH_REDIRECT_URI": "https://app/callback/google",
            "KAKAO_OAUTH_CLIENT_ID": "kakao-id",
            "KAKAO_OAUTH_CLIENT_SECRET": "kakao-secret",
            "KAKAO_OAUTH_REDIRECT_URI": "https://app/callback/kakao",
            "APPLE_OAUTH_CLIENT_ID": "apple-id",
            "APPLE_OAUTH_CLIENT_SECRET": "apple-secret",
            "APPLE_OAUTH_REDIRECT_URI": "https://app/callback/apple",
        },
    ):
        with pytest.raises(RuntimeError):
            load_settings()


def test_load_settings_fail_when_missing_oauth_env() -> None:
    with env_override(
        {
            "MBLOCK_API_BASE_URL": "https://mock.mblock",
            "MBLOCK_API_KEY": "secret",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "SECRET_KEY": "super-secret",
            "TURNSTILE_SECRET_KEY": "turnstile-secret",
        },
        clear=(
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GOOGLE_OAUTH_REDIRECT_URI",
        ),
    ):
        with pytest.raises(RuntimeError):
            load_settings()


def test_load_settings_uses_dev_defaults_when_dev_mode_enabled() -> None:
    keys = tuple(set(DEV_DEFAULTS) | {"GOOGLE_OAUTH_CLIENT_SECRET"})
    with env_override(
        {
            "AEGHASH_DEV_MODE": "1",
        },
        clear=keys,
    ):
        settings = load_settings()

    assert settings.mblock.base_url == DEV_DEFAULTS["MBLOCK_API_BASE_URL"]
    assert settings.mblock.api_key == DEV_DEFAULTS["MBLOCK_API_KEY"]
    assert settings.database_url == DEV_DEFAULTS["DATABASE_URL"]
    assert settings.secret_key == DEV_DEFAULTS["SECRET_KEY"]
    assert settings.oauth.google.client_id == DEV_DEFAULTS["GOOGLE_OAUTH_CLIENT_ID"]
    assert settings.turnstile.secret_key == DEV_DEFAULTS["TURNSTILE_SECRET_KEY"]
