"""Password hashing utilities using PBKDF2."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass

DEFAULT_SCHEME = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 150_000
DEFAULT_SALT_BYTES = 16


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Structured representation of a stored password hash."""

    scheme: str
    iterations: int
    salt: bytes
    digest: bytes

    def serialize(self) -> str:
        """Return the hash encoded as a string for storage."""
        salt_b64 = base64.b64encode(self.salt).decode("ascii")
        digest_b64 = base64.b64encode(self.digest).decode("ascii")
        return f"{self.scheme}${self.iterations}${salt_b64}${digest_b64}"

    @classmethod
    def deserialize(cls, value: str) -> "PasswordHash":
        """Parse the stored hash string."""
        try:
            scheme, iter_str, salt_b64, digest_b64 = value.split("$", 3)
            iterations = int(iter_str)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            digest = base64.b64decode(digest_b64.encode("ascii"))
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid password hash format.") from exc
        return cls(scheme=scheme, iterations=iterations, salt=salt, digest=digest)


def _derive_digest(password: str, *, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Generate a salted hash for the supplied password."""
    salt = os.urandom(DEFAULT_SALT_BYTES)
    digest = _derive_digest(password, salt=salt, iterations=iterations)
    return PasswordHash(
        scheme=DEFAULT_SCHEME,
        iterations=iterations,
        salt=salt,
        digest=digest,
    ).serialize()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against the stored hash."""
    parsed = PasswordHash.deserialize(stored_hash)
    if parsed.scheme != DEFAULT_SCHEME:
        raise ValueError(f"Unsupported password hash scheme: {parsed.scheme}")
    candidate = _derive_digest(password, salt=parsed.salt, iterations=parsed.iterations)
    return hmac.compare_digest(candidate, parsed.digest)
