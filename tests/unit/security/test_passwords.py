from aeghash.security.passwords import (
    PasswordHash,
    hash_password,
    verify_password,
)


def test_hash_password_produces_unique_salts() -> None:
    stored_a = hash_password("secret-password")
    stored_b = hash_password("secret-password")

    assert stored_a != stored_b
    assert verify_password("secret-password", stored_a)
    assert verify_password("secret-password", stored_b)


def test_password_hash_structure_roundtrip() -> None:
    stored = hash_password("another-secret")
    parsed = PasswordHash.deserialize(stored)

    assert parsed.scheme == "pbkdf2_sha256"
    assert parsed.iterations > 0
    assert len(parsed.salt) == 16
    assert len(parsed.digest) == 32
    assert parsed.serialize() == stored


def test_invalid_password_rejected() -> None:
    stored = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", stored) is False


def test_unsupported_hash_scheme_raises() -> None:
    fake_hash = PasswordHash(
        scheme="unknown",
        iterations=1,
        salt=b"salt",
        digest=b"digest",
    ).serialize()
    try:
        verify_password("anything", fake_hash)
        assert False, "verify_password should raise for unsupported scheme"
    except ValueError:
        pass
