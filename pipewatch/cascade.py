"""Cascade policy: suppress alerts if a parent/upstream pipeline recently failed."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.history import RunHistory


@dataclass
class CascadePolicy:
    upstream: list[str] = field(default_factory=list)
    window_minutes: int = 30
    state_dir: str = ".pipewatch"

    def is_enabled(self) -> bool:
        return len(self.upstream) > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "cascade suppression disabled"
        names = ", ".join(self.upstream)
        return f"suppress if upstream failed in last {self.window_minutes}m: {names}"


@dataclass
class CascadeResult:
    suppressed: bool
    upstream_pipeline: Optional[str] = None
    failed_at: Optional[datetime] = None

    def message(self) -> str:
        if not self.suppressed:
            return "no upstream failures detected"
        return (
            f"suppressed: upstream '{self.upstream_pipeline}' failed at "
            f"{self.failed_at.strftime('%Y-%m-%d %H:%M:%S') if self.failed_at else 'unknown'}"
        )


def check_cascade(policy: CascadePolicy, history: RunHistory) -> CascadeResult:
    """Return CascadeResult indicating whether alert should be suppressed."""
    if not policy.is_enabled():
        return CascadeResult(suppressed=False)

    cutoff = datetime.utcnow() - timedelta(minutes=policy.window_minutes)

    for upstream in policy.upstream:
        entry = history.last_for(upstream)
        if entry is None:
            continue
        if not entry.succeeded() and entry.started_at >= cutoff:
            return CascadeResult(
                suppressed=True,
                upstream_pipeline=upstream,
                failed_at=entry.started_at,
            )

    return CascadeResult(suppressed=False)
