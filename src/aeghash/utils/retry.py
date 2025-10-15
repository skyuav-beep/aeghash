"""Retry utilities with exponential backoff."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryConfig:
    attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0


def retry(config: RetryConfig, on_failure: Callable[[Exception, int], None] | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            delay = config.initial_delay
            for attempt in range(1, config.attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if on_failure:
                        on_failure(exc, attempt)
                    if attempt == config.attempts:
                        raise
                    time.sleep(delay)
                    delay *= config.backoff_factor
            raise RuntimeError("Retry exceeded attempts")
        return wrapper
    return decorator
