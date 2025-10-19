from aeghash.api.http import _mask_withdrawal_payload
from aeghash.core.repositories import SessionRecord
from aeghash.security.access import AccessContext, AccessPolicy


def test_mask_withdrawal_payload_applies_to_sensitive_fields() -> None:
    payload = {
        "request_id": "req-1",
        "wallet_id": "wallet-abcdef123456",
        "requested_by": "john.doe@example.com",
        "approved_by": "approver-1",
        "metadata": {
            "payout_email": "john.doe@example.com",
            "withdraw_address": "0x1234567890abcdef",
            "note": "no mask",
        },
    }
    session = SessionRecord(
        token="tok",
        user_id="support-1",
        roles=("support",),
        expires_at=0.0,
    )
    policy = AccessPolicy(AccessContext.from_session(session))

    masked = _mask_withdrawal_payload(payload, policy)

    assert masked["wallet_id"] != payload["wallet_id"]
    assert masked["requested_by"] != payload["requested_by"]
    assert masked["metadata"]["payout_email"] != payload["metadata"]["payout_email"]
    assert masked["metadata"]["withdraw_address"].startswith("0x12")
    assert "***" in masked["metadata"]["withdraw_address"]
    assert masked["metadata"]["note"] == "no mask"


def test_mask_withdrawal_payload_returns_original_for_privileged_role() -> None:
    payload = {
        "wallet_id": "wallet-xyz",
        "requested_by": "admin@example.com",
    }
    session = SessionRecord(
        token="tok",
        user_id="admin-1",
        roles=("admin",),
        expires_at=0.0,
    )
    policy = AccessPolicy(AccessContext.from_session(session))

    masked = _mask_withdrawal_payload(payload, policy)

    assert masked == payload
