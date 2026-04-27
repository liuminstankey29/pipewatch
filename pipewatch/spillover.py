"""Spillover policy: alert when a pipeline run exceeds a expected duration window."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpilloverPolicy:
    """Detect runs that spill over their expected maximum duration."""

    warn_seconds: Optional[float] = None
    max_seconds: Optional[float] = None

    def is_enabled(self) -> bool:
        return self.warn_seconds is not None or self.max_seconds is not None

    def describe(self) -> str:
        if not self.is_enabled():
            return "spillover: disabled"
        parts = []
        if self.warn_seconds is not None:
            parts.append(f"warn>{self.warn_seconds}s")
        if self.max_seconds is not None:
            parts.append(f"max>{self.max_seconds}s")
        return "spillover: " + ", ".join(parts)


@dataclass
class SpilloverResult:
    elapsed: float
    warn_seconds: Optional[float]
    max_seconds: Optional[float]
    warned: bool = field(init=False)
    breached: bool = field(init=False)

    def __post_init__(self) -> None:
        self.warned = (
            self.warn_seconds is not None and self.elapsed >= self.warn_seconds
        )
        self.breached = (
            self.max_seconds is not None and self.elapsed >= self.max_seconds
        )

    def message(self) -> str:
        if self.breached:
            return (
                f"Pipeline exceeded max duration "
                f"({self.elapsed:.1f}s >= {self.max_seconds}s)"
            )
        if self.warned:
            return (
                f"Pipeline approaching max duration "
                f"({self.elapsed:.1f}s >= {self.warn_seconds}s warn threshold)"
            )
        return f"Pipeline within expected duration ({self.elapsed:.1f}s)"


def evaluate_spillover(
    policy: SpilloverPolicy, elapsed: float
) -> Optional[SpilloverResult]:
    """Return a SpilloverResult if the policy is enabled, else None."""
    if not policy.is_enabled():
        return None
    return SpilloverResult(
        elapsed=elapsed,
        warn_seconds=policy.warn_seconds,
        max_seconds=policy.max_seconds,
    )
