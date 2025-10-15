from aeghash.utils.notifications import NotificationMessage


def test_notification_message_dataclass():
    message = NotificationMessage(subject="Test", body="Body")
    assert message.subject == "Test"
    assert message.body == "Body"
