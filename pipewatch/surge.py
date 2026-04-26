"""Surge detection: alert when run frequency spikes above a rolling baseline."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

log = logging.getLogger(__name__)


@dataclass
class SurgePolicy:
    max_runs: int = 0          # max allowed runs in the window; 0 = disabled
    window_minutes: int = 60   # rolling window length in minutes
    pipeline: str = ""

    def is_enabled(self) -> bool:
        return self.max_runs > 0 and self.window_minutes > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "surge detection disabled"
        return (
            f"surge detection: max {self.max_runs} runs "
            f"per {self.window_minutes}m window"
        )


@dataclass
class SurgeResult:
    suppressed: bool
    run_count: int
    max_runs: int
    window_minutes: int
    message: str = field(default="")

    def __post_init__(self) -> None:
        if not self.message:
            if self.suppressed:
                self.message = (
                    f"surge detected: {self.run_count} runs in last "
                    f"{self.window_minutes}m (max {self.max_runs})"
                )
            else:
                self.message = (
                    f"{self.run_count}/{self.max_runs} runs in last "
                    f"{self.window_minutes}m"
                )


def check_surge(
    policy: SurgePolicy,
    history,  # RunHistory
    pipeline: Optional[str] = None,
    now: Optional[datetime] = None,
) -> SurgeResult:
    """Return a SurgeResult indicating whether the run should be suppressed."""
    if not policy.is_enabled():
        return SurgeResult(
            suppressed=False,
            run_count=0,
            max_runs=policy.max_runs,
            window_minutes=policy.window_minutes,
        )

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=policy.window_minutes)
    name = pipeline or policy.pipeline

    entries = history.last_for(pipeline=name) if name else history.all()
    recent = [
        e for e in entries
        if datetime.fromisoformat(e.started_at) >= cutoff
    ]
    run_count = len(recent)
    suppressed = run_count >= policy.max_runs

    if suppressed:
        log.warning(
            "Surge detected for %s: %d runs in %dm window (max %d)",
            name or "<all>",
            run_count,
            policy.window_minutes,
            policy.max_runs,
        )

    return SurgeResult(
        suppressed=suppressed,
        run_count=run_count,
        max_runs=policy.max_runs,
        window_minutes=policy.window_minutes,
    )
