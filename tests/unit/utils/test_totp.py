import time

from aeghash.utils import totp


def test_generate_secret_unique():
    secret1 = totp.generate_secret()
    secret2 = totp.generate_secret()
    assert secret1 != secret2
    assert len(secret1) >= 16


def test_totp_generation_and_verification():
    secret = totp.generate_secret()
    timestamp = int(time.time())
    code = totp.totp(secret, timestamp=timestamp)
    assert totp.verify_totp(secret, code, window=1, step=30, digits=6)


def test_totp_verification_rejects_invalid_code():
    secret = totp.generate_secret()
    assert not totp.verify_totp(secret, "abcdef")
