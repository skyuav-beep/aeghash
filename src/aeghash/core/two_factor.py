"""Two-factor authentication service."""

from __future__ import annotations

import hashlib
import secrets
import string
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Tuple

from aeghash.core.repositories import TwoFactorRecord, TwoFactorRepository
from aeghash.utils import totp
from aeghash.utils.crypto import EncryptionError, decrypt_secret, encrypt_secret


@dataclass(slots=True)
class TwoFactorStatus:
    user_id: str
    enabled: bool
    secret: str | None
    recovery_codes: tuple[str, ...] = ()


class TwoFactorService:
    """Manage two-factor secrets and verification."""

    def __init__(
        self,
        repository: TwoFactorRepository,
        *,
        encryptor: Callable[[str], str] = encrypt_secret,
        decryptor: Callable[[str], str] = decrypt_secret,
        event_hook: Callable[[str, Mapping[str, object]], None] | None = None,
    ) -> None:
        self._repository = repository
        self._encrypt = encryptor
        self._decrypt = decryptor
        self._event_hook = event_hook

    def enable(self, user_id: str) -> TwoFactorStatus:
        secret = totp.generate_secret()
        recovery_codes = self._generate_recovery_codes()
        stored_secret = self._protect_secret(secret)
        record = TwoFactorRecord(
            user_id=user_id,
            secret=stored_secret,
            enabled=True,
            updated_at=time.time(),
            recovery_codes=tuple(self._hash_code(code) for code in recovery_codes),
        )
        self._repository.save(record)
        self._emit_event(
            "two_factor.enabled",
            {
                "provider": "two_factor",
                "subject": user_id,
                "actor_id": user_id,
            },
        )
        return TwoFactorStatus(
            user_id=user_id,
            enabled=True,
            secret=secret,
            recovery_codes=recovery_codes,
        )

    def disable(self, user_id: str, *, actor_id: str | None = None) -> bool:
        record = self._repository.get(user_id)
        if not record or not record.enabled:
            return False
        self._repository.disable(user_id)
        self._emit_event(
            "two_factor.disabled",
            {
                "provider": "two_factor",
                "subject": user_id,
                "actor_id": actor_id or user_id,
            },
        )
        return True

    def is_enabled(self, user_id: str) -> bool:
        record = self._repository.get(user_id)
        return bool(record and record.enabled)

    def initiate_challenge(self, user_id: str) -> None:
        # For TOTP there is no server-side challenge to initiate.
        # Method kept for interface compatibility.
        if not self.is_enabled(user_id):
            raise ValueError("Two-factor authentication is not enabled for this user.")

    def verify(self, user_id: str, code: str) -> bool:
        record = self._repository.get(user_id)
        if not record or not record.enabled:
            raise ValueError("Two-factor authentication is not enabled for this user.")
        secret = self._reveal_secret(record.secret)
        return totp.verify_totp(secret, code)

    # Adapter for OAuthFlowService interface
    def verify_code(self, user_id: str, code: str) -> bool:
        return self.verify(user_id, code)

    def list_recovery_code_hashes(self, user_id: str) -> tuple[str, ...]:
        record = self._repository.get(user_id)
        if not record:
            return ()
        return tuple(record.recovery_codes)

    def use_recovery_code(self, user_id: str, code: str) -> bool:
        record = self._repository.get(user_id)
        if not record or not record.recovery_codes:
            return False

        hashed = self._hash_code(code)
        if hashed not in record.recovery_codes:
            return False

        remaining = tuple(value for value in record.recovery_codes if value != hashed)
        updated_record = TwoFactorRecord(
            user_id=record.user_id,
            secret=record.secret,
            enabled=record.enabled,
            updated_at=time.time(),
            recovery_codes=remaining,
        )
        self._repository.save(updated_record)
        return True

    def _protect_secret(self, secret: str) -> str:
        try:
            return self._encrypt(secret)
        except EncryptionError:
            return secret

    def _reveal_secret(self, secret: str) -> str:
        try:
            return self._decrypt(secret)
        except EncryptionError:
            return secret

    @staticmethod
    def _generate_recovery_codes(count: int = 5, length: int = 10) -> Tuple[str, ...]:
        alphabet = string.ascii_uppercase + string.digits
        return tuple(
            "".join(secrets.choice(alphabet) for _ in range(length))
            for _ in range(count)
        )

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def _emit_event(self, name: str, payload: Mapping[str, object]) -> None:
        if self._event_hook is None:
            return
        self._event_hook(name, payload)
