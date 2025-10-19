from aeghash.adapters.oauth import AppleOAuthClient, GoogleOAuthClient, KakaoOAuthClient
from aeghash.adapters.oauth_stub import DEV_OAUTH_PROFILES, DevOAuthTransport
from aeghash.config import OAuthProviderSettings


def make_settings() -> OAuthProviderSettings:
    return OAuthProviderSettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="https://app/callback",
    )


def test_dev_oauth_transport_supports_google_client() -> None:
    transport = DevOAuthTransport("google")
    client = GoogleOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="dev-code")

    profile = DEV_OAUTH_PROFILES["google"]
    assert result.profile.subject == profile.subject
    assert result.profile.email == profile.email
    transport.close()


def test_dev_oauth_transport_supports_kakao_client() -> None:
    transport = DevOAuthTransport("kakao")
    client = KakaoOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="dev-code")

    profile = DEV_OAUTH_PROFILES["kakao"]
    assert result.profile.subject == str(profile.subject)
    assert result.profile.email == profile.email
    transport.close()


def test_dev_oauth_transport_supports_apple_client() -> None:
    transport = DevOAuthTransport("apple")
    client = AppleOAuthClient(transport=transport, settings=make_settings())

    result = client.authenticate(code="dev-code")

    profile = DEV_OAUTH_PROFILES["apple"]
    assert result.profile.subject == profile.subject
    assert result.profile.email == profile.email
    assert result.token.id_token is not None
    transport.close()
