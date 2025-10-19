import logging
from typing import List, Mapping

import pytest

from aeghash.utils.observability import AuthMetricCollector, AuthMetricExporter, LoggingAuthMetricExporter


def test_metric_collector_counts_events() -> None:
    collector = AuthMetricCollector()

    collector.handle_event("auth.start", {"provider": "google"})
    collector.handle_event("auth.success", {"provider": "google", "subject": "user-1"})
    collector.handle_event("auth.success", {"provider": "google", "subject": "user-2"})
    collector.handle_event("auth.error", {"provider": "kakao", "reason": "invalid_code"})

    assert collector.total("auth.start", "google") == 1
    assert collector.total("auth.success", "google") == 2
    assert collector.total("auth.error", "kakao") == 1
    assert collector.total("auth.error", "google") == 0
    assert collector.success_subject("google") == "user-2"
    snapshot = collector.snapshot()
    assert snapshot["auth.success"]["google"] == 2
    assert snapshot["auth.error"]["kakao"] == 1


class StubExporter(AuthMetricExporter):
    def __init__(self) -> None:
        self.events: List[tuple[str, Mapping[str, object]]] = []

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        self.events.append((name, dict(payload)))


def test_metric_collector_invokes_exporters() -> None:
    collector = AuthMetricCollector()
    exporter = StubExporter()
    collector.register_exporter(exporter)

    collector.handle_event("auth.success", {"provider": "google", "subject": "user"})

    assert exporter.events == [("auth.success", {"provider": "google", "subject": "user"})]
    assert list(collector.exporters) == [exporter]


def test_logging_auth_metric_exporter_logs_event(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("test.logger")
    exporter = LoggingAuthMetricExporter(logger)

    with caplog.at_level(logging.INFO, logger="test.logger"):
        exporter.handle_event("auth.error", {"provider": "google", "reason": "invalid"})

    assert any("auth event" in record.message for record in caplog.records)
