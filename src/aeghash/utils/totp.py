"""Minimal TOTP helper implementation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time


def generate_secret(length: int = 20) -> str:
    """Generate a base32 encoded secret."""
    random_bytes = os.urandom(length)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")


def _time_counter(timestamp: float | None = None, step: int = 30) -> int:
    current_time = int(timestamp or time.time())
    return current_time // step


def totp(secret: str, *, timestamp: float | None = None, digits: int = 6, step: int = 30) -> str:
    """Generate a TOTP code for the given secret."""
    padding = (-len(secret)) % 8
    key = base64.b32decode(secret.upper() + "=" * padding)
    counter = _time_counter(timestamp, step)
    counter_bytes = struct.pack(">Q", counter)
    digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def verify_totp(secret: str, code: str, *, window: int = 1, digits: int = 6, step: int = 30) -> bool:
    """Verify a TOTP code within the specified window."""
    if not code or not code.isdigit():
        return False

    current_counter = _time_counter(step=step)
    for offset in range(-window, window + 1):
        candidate = totp(secret, timestamp=(current_counter + offset) * step, digits=digits, step=step)
        if hmac.compare_digest(candidate, code):
            return True
    return False
