"""Timeout utilities for pipeline execution."""
from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional


class TimeoutExpired(Exception):
    """Raised when a pipeline exceeds its allowed runtime."""

    def __init__(self, seconds: int) -> None:
        self.seconds = seconds
        super().__init__(f"Pipeline timed out after {seconds}s")


@dataclass
class TimeoutPolicy:
    seconds: Optional[int] = None  # None means no timeout
    kill_on_expire: bool = True

    def is_enabled(self) -> bool:
        return self.seconds is not None and self.seconds > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "no timeout"
        return f"{self.seconds}s timeout"


def policy_from_config(cfg: object) -> TimeoutPolicy:
    """Build a TimeoutPolicy from a Config object."""
    seconds = getattr(cfg, "timeout", None)
    return TimeoutPolicy(seconds=seconds)


@contextmanager
def timeout_context(policy: TimeoutPolicy):
    """Context manager that enforces a TimeoutPolicy using SIGALRM.

    Only available on Unix-like systems.
    """
    if not policy.is_enabled():
        yield
        return

    def _handler(signum, frame):  # noqa: ANN001
        raise TimeoutExpired(policy.seconds)  # type: ignore[arg-type]

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(policy.seconds)  # type: ignore[arg-type]
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
