"""Encryption utilities for sensitive secrets (e.g., TOTP seeds)."""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


class EncryptionError(RuntimeError):
    """Raised when encryption or decryption fails."""


def _resolve_key() -> bytes:
    key = os.environ.get("AEGHASH_ENCRYPTION_KEY")
    if not key:
        raise EncryptionError("AEGHASH_ENCRYPTION_KEY must be defined.")
    try:
        return key.encode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        raise EncryptionError("Invalid encryption key encoding.") from exc


def encrypt_secret(plaintext: str) -> str:
    """Encrypt the given plaintext using Fernet symmetric key encryption."""
    key = _resolve_key()
    try:
        cipher = Fernet(key)
    except Exception as exc:  # pragma: no cover - defensive
        raise EncryptionError("Failed to initialize cipher.") from exc
    token = cipher.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Decrypt the given ciphertext using Fernet symmetric key encryption."""
    key = _resolve_key()
    try:
        cipher = Fernet(key)
        plaintext = cipher.decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise EncryptionError("Invalid encryption token.") from exc
    return plaintext.decode("utf-8")
