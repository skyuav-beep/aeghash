"""Utilities for masking sensitive data in responses."""

from __future__ import annotations

import re


def mask_email(value: str | None) -> str:
    if not value or "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[:2] + "*" * max(1, len(local) - 2)
    return f"{masked_local}@{domain}"


PHONE_PATTERN = re.compile(r"\d")


def mask_phone(value: str | None) -> str:
    if not value:
        return "***"
    digits = [c for c in value if c.isdigit()]
    if len(digits) <= 4:
        return "*" * len(value)
    masked_digits = "*" * (len(digits) - 4) + "".join(digits[-4:])
    result = []
    digit_index = 0
    for char in value:
        if char.isdigit():
            result.append(masked_digits[digit_index])
            digit_index += 1
        else:
            result.append(char)
    return "".join(result)


def mask_wallet_address(value: str | None) -> str:
    if not value:
        return "***"
    if len(value) <= 8:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    return f"{value[:4]}***{value[-4:]}"


def mask_identifier(value: str | None) -> str:
    if not value:
        return "***"
    if "@" in value:
        return mask_email(value)
    if len(value) <= 4:
        return value[0] + "*" * (len(value) - 1)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


__all__ = ["mask_email", "mask_phone", "mask_wallet_address", "mask_identifier"]
