"""Notification interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class NotificationMessage:
    subject: str
    body: str


class Notifier(Protocol):
    def send(self, message: NotificationMessage) -> None:
        ...
