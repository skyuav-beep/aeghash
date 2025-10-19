"""Application bootstrap utilities for service wiring."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from aeghash.config import AppSettings, is_dev_mode, load_settings
from aeghash.infrastructure.audit import LoginAuditLogger
from aeghash.infrastructure.bootstrap import ServiceContainer, bootstrap_services, shutdown_services
from aeghash.utils.observability import (
    AuthEventDispatcher,
    AuthMetricCollector,
    AuthMetricExporter,
    LoggingAuthMetricExporter,
)


@dataclass(slots=True)
class Application:
    """Top-level application object containing core services and metrics."""

    container: ServiceContainer
    metrics: AuthMetricCollector


def create_application(
    settings: AppSettings | None = None,
    *,
    logger: logging.Logger | None = None,
    exporters: Iterable[AuthMetricExporter] | None = None,
    enable_logging_exporter: bool = True,
) -> Application:
    """Create an application instance from configuration."""

    resolved_settings = settings or load_settings()
    metrics = AuthMetricCollector()

    if enable_logging_exporter:
        metrics.register_exporter(LoggingAuthMetricExporter(logger))

    transport_factory = None
    if is_dev_mode():
        from aeghash.adapters.oauth_stub import DevOAuthTransport

        def _dev_transport_factory(provider: str):
            return DevOAuthTransport(provider)

        transport_factory = _dev_transport_factory

    if exporters:
        for exporter in exporters:
            metrics.register_exporter(exporter)

    dispatcher = AuthEventDispatcher()
    dispatcher.register(metrics.handle_event)

    container = bootstrap_services(
        resolved_settings,
        event_hook=dispatcher.handle_event,
        logger=logger,
        transport_factory=transport_factory,
    )
    audit_logger = LoginAuditLogger(container.session_manager)
    dispatcher.register(audit_logger.handle_event)
    container.audit_logger = audit_logger
    return Application(container=container, metrics=metrics)


def shutdown_application(app: Application) -> None:
    """Gracefully shutdown application services."""
    shutdown_services(app.container)
