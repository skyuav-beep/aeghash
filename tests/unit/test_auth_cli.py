import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from aeghash.application import Application
from aeghash.utils.observability import AuthMetricCollector

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "auth_cli.py"
spec = importlib.util.spec_from_file_location("auth_cli", MODULE_PATH)
assert spec and spec.loader
auth_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth_cli)


class StubAuthService:
    def __init__(self, metrics: AuthMetricCollector) -> None:
        self.metrics = metrics
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    def authenticate(self, *, provider: str, code: str):
        self.calls.append((provider, code))
        self.metrics.handle_event("auth.success", {"provider": provider, "subject": "user"})
        return SimpleNamespace(profile=SimpleNamespace(provider=provider, subject="user"))

    def close(self) -> None:
        self.closed = True


def make_application() -> Application:
    metrics = AuthMetricCollector()
    service = StubAuthService(metrics)
    container = SimpleNamespace(auth_service=service, settings=None)
    return Application(container=container, metrics=metrics)


def test_auth_cli_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    app = make_application()
    shutdown_called: dict[str, bool] = {}

    monkeypatch.setattr(auth_cli, "create_application", lambda **kwargs: app)

    def fake_shutdown(application: Application) -> None:
        shutdown_called["called"] = True
        application.container.auth_service.close()  # type: ignore[attr-defined]

    monkeypatch.setattr(auth_cli, "shutdown_application", fake_shutdown)

    exit_code = auth_cli.main(["google", "code123", "--metrics", "--no-logging-exporter"])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Authenticated with provider 'google'" in stdout
    assert '"auth.success"' in stdout
    assert app.container.auth_service.calls == [("google", "code123")]  # type: ignore[attr-defined]
    assert shutdown_called.get("called") is True
    assert app.metrics.total("auth.success", "google") == 1


def test_auth_cli_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics = AuthMetricCollector()

    class FailingAuthService(StubAuthService):
        def authenticate(self, *, provider: str, code: str):
            raise RuntimeError("boom")

    service = FailingAuthService(metrics)
    container = SimpleNamespace(auth_service=service, settings=None)
    app = Application(container=container, metrics=metrics)
    shutdown_called: dict[str, bool] = {}

    monkeypatch.setattr(auth_cli, "create_application", lambda **kwargs: app)

    def fake_shutdown(application: Application) -> None:
        shutdown_called["called"] = True

    monkeypatch.setattr(auth_cli, "shutdown_application", fake_shutdown)

    exit_code = auth_cli.main(["google", "code123", "--no-logging-exporter"])
    assert exit_code == 1
    assert shutdown_called.get("called") is True
