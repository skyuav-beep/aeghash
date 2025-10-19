"""Utility helpers to work with the UI design token JSON bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

TOKENS_ROOT = Path(__file__).resolve().parents[3] / "tokens"


class TokenBundleNotFoundError(FileNotFoundError):
    """Raised when the requested token bundle does not exist."""


class TokenPathError(KeyError):
    """Raised when a nested token path cannot be resolved."""


@dataclass(frozen=True)
class TokenBundle:
    """Container exposing metadata and payload for a token category."""

    category: str
    meta: Mapping[str, Any]
    payload: Mapping[str, Any]
    schema: str | None = None

    def get(self, path: str, *, default: Any = None) -> Any:
        """Return a token value by dotted path, falling back to default when provided."""
        try:
            return _resolve_path(self.payload, path)
        except TokenPathError:
            if default is not None:
                return default
            raise


def available_categories() -> tuple[str, ...]:
    """Return the discoverable token categories (json files under /tokens)."""
    if not TOKENS_ROOT.exists():
        return ()
    categories: list[str] = []
    for path in sorted(TOKENS_ROOT.glob("*.json")):
        categories.append(path.stem)
    return tuple(categories)


@lru_cache(maxsize=16)
def load_bundle(category: str) -> TokenBundle:
    """Load and cache the requested token bundle."""
    path = TOKENS_ROOT / f"{category}.json"
    if not path.exists():
        raise TokenBundleNotFoundError(f"Token bundle '{category}' not found at {path}")

    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ValueError(f"Token bundle '{category}' must be a JSON object")

    schema = raw.get("$schema")
    meta = raw.get("meta", {})
    payload = {key: value for key, value in raw.items() if key not in {"$schema", "meta"}}

    if not payload:
        raise ValueError(f"Token bundle '{category}' payload is empty")

    return TokenBundle(category=category, meta=meta, payload=payload, schema=schema)


def get_token(category: str, path: str) -> Any:
    """Convenience accessor for a single token using dotted path traversal."""
    bundle = load_bundle(category)
    return bundle.get(path)


def _resolve_path(source: Mapping[str, Any], path: str) -> Any:
    cursor: Any = source
    for segment in path.split("."):
        if isinstance(cursor, Mapping) and segment in cursor:
            cursor = cursor[segment]
            continue
        raise TokenPathError(f"Unable to resolve '{path}' (failed at '{segment}')")
    return cursor


__all__ = [
    "TokenBundle",
    "TokenBundleNotFoundError",
    "TokenPathError",
    "available_categories",
    "get_token",
    "load_bundle",
]
