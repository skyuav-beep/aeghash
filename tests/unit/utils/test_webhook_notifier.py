import httpx

from aeghash.utils.notifications import NotificationMessage
from aeghash.utils.webhook_notifier import WebhookNotifier


def test_webhook_notifier_sends(monkeypatch):
    called = {}

    class MockClient:
        def post(self, url, json=None):
            called['url'] = url
            called['json'] = json
            return httpx.Response(200, request=httpx.Request("POST", url))

    notifier = WebhookNotifier(url="https://example.com/hook", client=MockClient())
    notifier.send(NotificationMessage(subject="Test", body="Body"))

    assert called['url'] == "https://example.com/hook"
    assert called['json']['subject'] == "Test"
