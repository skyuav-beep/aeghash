"""Webhook notifier implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from aeghash.utils.notifications import NotificationMessage, Notifier


@dataclass
class WebhookNotifier(Notifier):
    url: str
    client: Optional[httpx.Client] = None

    def send(self, message: NotificationMessage) -> None:
        payload = {"subject": message.subject, "body": message.body}
        if self.client:
            response = self.client.post(self.url, json=payload)
        else:
            with httpx.Client() as client:
                response = client.post(self.url, json=payload)
        response.raise_for_status()
