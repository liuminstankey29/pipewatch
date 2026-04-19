"""Exponential back-off policy for pipeline retries."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterator, Optional


@dataclass
class BackoffPolicy:
    base: float = 2.0          # seconds for first delay
    multiplier: float = 2.0    # growth factor
    max_delay: float = 300.0   # cap in seconds
    jitter: float = 0.0        # max random jitter in seconds
    max_attempts: int = 5

    def __post_init__(self) -> None:
        if self.base < 0:
            raise ValueError("base must be >= 0")
        if self.multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        if self.max_delay < self.base:
            raise ValueError("max_delay must be >= base")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

    def is_enabled(self) -> bool:
        return self.max_attempts > 1

    def describe(self) -> str:
        if not self.is_enabled():
            return "backoff disabled"
        return (
            f"backoff base={self.base}s multiplier={self.multiplier}x "
            f"cap={self.max_delay}s attempts={self.max_attempts}"
        )

    def delays(self) -> Iterator[float]:
        """Yield delay seconds before each retry (not before first attempt)."""
        import random
        delay = self.base
        for _ in range(self.max_attempts - 1):
            j = random.uniform(0, self.jitter) if self.jitter else 0.0
            yield min(delay + j, self.max_delay)
            delay = min(delay * self.multiplier, self.max_delay)

    def run(self, fn: Callable[[], bool], _sleep: Callable[[float], None] = time.sleep) -> bool:
        """Call fn() up to max_attempts times; return True on first success."""
        for attempt, delay in enumerate(self.delays(), start=1):
            if fn():
                return True
            _sleep(delay)
        return fn()
