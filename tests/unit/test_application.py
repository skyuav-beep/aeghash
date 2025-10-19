import logging

from aeghash.adapters.oauth import OAuthProfile, OAuthResult, OAuthToken
from aeghash.application import Application, create_application, shutdown_application
from aeghash.config import AppSettings, HashDamSettings, MBlockSettings, OAuthProviderSettings, OAuthSettings, TurnstileSettings
from aeghash.infrastructure.bootstrap import ServiceContainer


class StubAuthService:
    def __init__(self, hook):
        self._hook = hook
        self.closed = False

    def authenticate(self, *, provider: str, code: str) -> OAuthResult:
        if self._hook:
            self._hook("auth.success", {"provider": provider, "subject": "user"})
        return OAuthResult(
            token=OAuthToken(
                access_token="token",
                token_type="Bearer",
                expires_in=None,
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

    def close(self) -> None:
        self.closed = True


class StubSessionManager:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.disposed = False

    def dispose(self) -> None:
        self.disposed = True


def make_settings() -> AppSettings:
    provider_settings = OAuthProviderSettings(
        client_id="client",
        client_secret="secret",
        redirect_uri="https://app/callback",
    )
    oauth = OAuthSettings(google=provider_settings, kakao=provider_settings, apple=provider_settings)
    return AppSettings(
        hashdam=HashDamSettings(),
        mblock=MBlockSettings(base_url="https://mock", api_key="key"),
        oauth=oauth,
        turnstile=TurnstileSettings(secret_key="turnstile-secret"),
        database_url="sqlite+pysqlite:///:memory:",
        secret_key="secret",
    )


def test_create_application_wires_container(monkeypatch):
    captured_hook = {}

    def stub_bootstrap(settings, *, event_hook=None, logger=None, transport_factory=None):
        captured_hook["event_hook"] = event_hook
        captured_hook["logger"] = logger
        container = ServiceContainer(
            settings=settings,
            session_manager=StubSessionManager(settings.database_url),
            auth_service=StubAuthService(event_hook),
            event_hook=event_hook,
        )
        return container

    shutdown_called = {}

    def stub_shutdown(container):
        shutdown_called["container"] = container
        container.auth_service.close()
        container.session_manager.dispose()

    monkeypatch.setattr("aeghash.application.bootstrap_services", stub_bootstrap)
    monkeypatch.setattr("aeghash.application.shutdown_services", stub_shutdown)

    class StubAuditLogger:
        def __init__(self, session_manager):
            self.session_manager = session_manager
            self.events = []

        def handle_event(self, name, payload):
            self.events.append((name, dict(payload)))

    monkeypatch.setattr("aeghash.application.LoginAuditLogger", StubAuditLogger)

    settings = make_settings()
    logger = logging.getLogger("test")
    app = create_application(settings=settings, logger=logger, enable_logging_exporter=False)

    assert isinstance(app, Application)
    assert app.container.settings is settings
    assert captured_hook["event_hook"] is not None
    assert captured_hook["logger"] is logger
    assert app.container.audit_logger is not None

    app.container.auth_service.authenticate(provider="google", code="auth-code")
    assert app.metrics.total("auth.success", "google") == 1
    assert app.container.audit_logger.events[-1][0] == "auth.success"  # type: ignore[index]

    shutdown_application(app)
    assert shutdown_called["container"] is app.container
    assert app.container.auth_service.closed
    assert app.container.session_manager.disposed


def test_create_application_loads_settings(monkeypatch):
    settings = make_settings()
    load_called = {}

    monkeypatch.setattr("aeghash.application.load_settings", lambda: settings)

    def stub_bootstrap(settings, *, event_hook=None, logger=None, transport_factory=None):
        load_called["settings"] = settings
        return ServiceContainer(
            settings=settings,
            session_manager=StubSessionManager(settings.database_url),
            auth_service=StubAuthService(event_hook),
            event_hook=event_hook,
        )

    monkeypatch.setattr("aeghash.application.bootstrap_services", stub_bootstrap)
    monkeypatch.setattr("aeghash.application.shutdown_services", lambda container: None)

    monkeypatch.setattr(
        "aeghash.application.LoginAuditLogger",
        lambda session_manager: type("StubAudit", (), {"handle_event": lambda self, name, payload: None})(),
    )

    app = create_application(enable_logging_exporter=False)
    assert load_called["settings"] is settings
    assert app.container.settings is settings


def test_create_application_registers_logging_exporter(monkeypatch):
    settings = make_settings()

    def stub_bootstrap(settings, *, event_hook=None, logger=None, transport_factory=None):
        return ServiceContainer(
            settings=settings,
            session_manager=StubSessionManager(settings.database_url),
            auth_service=StubAuthService(event_hook),
            event_hook=event_hook,
        )

    monkeypatch.setattr("aeghash.application.bootstrap_services", stub_bootstrap)
    monkeypatch.setattr("aeghash.application.shutdown_services", lambda container: None)

    monkeypatch.setattr(
        "aeghash.application.LoginAuditLogger",
        lambda session_manager: type("StubAudit", (), {"handle_event": lambda self, name, payload: None})(),
    )

    app = create_application(settings=settings)
    exporters = list(app.metrics.exporters)
    assert exporters, "logging exporter should be registered by default"


def test_create_application_uses_dev_transport(monkeypatch):
    monkeypatch.setenv("AEGHASH_DEV_MODE", "1")

    captured_transport = {}

    def stub_bootstrap(settings, *, event_hook=None, logger=None, transport_factory=None):
        assert transport_factory is not None
        transport = transport_factory("google")
        from aeghash.adapters.oauth_stub import DevOAuthTransport

        assert isinstance(transport, DevOAuthTransport)
        captured_transport["transport"] = transport
        return ServiceContainer(
            settings=settings,
            session_manager=StubSessionManager(settings.database_url),
            auth_service=StubAuthService(event_hook),
            event_hook=event_hook,
        )

    monkeypatch.setattr("aeghash.application.bootstrap_services", stub_bootstrap)
    monkeypatch.setattr("aeghash.application.shutdown_services", lambda container: None)
    monkeypatch.setattr(
        "aeghash.application.LoginAuditLogger",
        lambda session_manager: type("StubAudit", (), {"handle_event": lambda self, name, payload: None})(),
    )

    try:
        create_application(settings=make_settings(), enable_logging_exporter=False)
    finally:
        monkeypatch.delenv("AEGHASH_DEV_MODE")

    assert "transport" in captured_transport
