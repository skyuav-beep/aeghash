"""Observability helpers for authentication events."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Protocol


AuthEventHandler = Callable[[str, Mapping[str, object]], None]


class AuthEventDispatcher:
    """Simple dispatcher to fan out authentication events to multiple handlers."""

    def __init__(self) -> None:
        self._handlers: List[AuthEventHandler] = []

    def register(self, handler: AuthEventHandler) -> None:
        self._handlers.append(handler)

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        for handler in list(self._handlers):
            handler(name, payload)


class AuthMetricExporter(Protocol):
    """Exporter interface for authentication metrics."""

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        ...


@dataclass
class AuthMetricCollector:
    """Collect and dispatch metrics derived from authentication events."""

    counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_subject_by_provider: Dict[str, str] = field(default_factory=dict)
    _exporters: List[AuthMetricExporter] = field(default_factory=list)

    def register_exporter(self, exporter: AuthMetricExporter) -> None:
        """Register an exporter to receive auth events."""
        self._exporters.append(exporter)

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        provider = str(payload.get("provider", "unknown"))
        provider_counts = self.counts.setdefault(name, {})
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

        subject = payload.get("subject")
        if name == "auth.success" and isinstance(subject, str):
            self.last_subject_by_provider[provider] = subject

        for exporter in self._exporters:
            exporter.handle_event(name, payload)

    def total(self, event: str, provider: str) -> int:
        """Return the count for the specified event/provider."""
        return self.counts.get(event, {}).get(provider, 0)

    def success_subject(self, provider: str) -> str | None:
        """Return the most recent subject for a provider."""
        return self.last_subject_by_provider.get(provider)

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        """Return a shallow copy of the collected metrics."""
        return {event: dict(values) for event, values in self.counts.items()}

    @property
    def exporters(self) -> Iterable[AuthMetricExporter]:
        """Expose registered exporters."""
        return tuple(self._exporters)


class LoggingAuthMetricExporter(AuthMetricExporter):
    """Exporter that logs authentication events."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        self._logger.info("auth event", extra={"event": name, "payload": dict(payload)})


class OpenTelemetryAuthExporter(AuthMetricExporter):
    """Exporter that forwards metrics to OpenTelemetry counters."""

    def __init__(self, meter=None) -> None:
        try:
            if meter is None:
                from opentelemetry.metrics import get_meter_provider  # type: ignore[import-not-found]

                meter = get_meter_provider().get_meter(__name__)
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("opentelemetry package is required for OpenTelemetryAuthExporter") from exc

        self._success_counter = meter.create_counter(  # type: ignore[attr-defined]
            name="auth_success_total",
            unit="1",
            description="Number of successful OAuth authentications",
        )
        self._error_counter = meter.create_counter(  # type: ignore[attr-defined]
            name="auth_error_total",
            unit="1",
            description="Number of failed OAuth authentications",
        )

    def handle_event(self, name: str, payload: Mapping[str, object]) -> None:
        provider = str(payload.get("provider", "unknown"))
        attributes: MutableMapping[str, object] = {"provider": provider}
        if name == "auth.success":
            self._success_counter.add(1, attributes)  # type: ignore[attr-defined]
        elif name == "auth.error":
            attributes["reason"] = payload.get("reason", "unknown")
            self._error_counter.add(1, attributes)  # type: ignore[attr-defined]
