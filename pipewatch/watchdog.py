"""Watchdog: detect stale/stuck pipelines that haven't run recently."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.history import RunHistory


@dataclass
class WatchdogPolicy:
    pipeline: str
    max_silence_minutes: int  # alert if no successful run within this window

    def is_enabled(self) -> bool:
        return self.max_silence_minutes > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "watchdog disabled"
        return f"alert if no success in {self.max_silence_minutes}m"


@dataclass
class WatchdogResult:
    pipeline: str
    stale: bool
    last_success: Optional[datetime]
    max_silence_minutes: int

    def message(self) -> str:
        if not self.stale:
            return f"{self.pipeline}: last success {self.last_success}"
        if self.last_success is None:
            return f"{self.pipeline}: no successful run on record"
        age = int((datetime.utcnow() - self.last_success).total_seconds() / 60)
        return (
            f"{self.pipeline}: no success in {age}m "
            f"(threshold {self.max_silence_minutes}m)"
        )


def check_watchdog(policy: WatchdogPolicy, history: RunHistory) -> WatchdogResult:
    """Return a WatchdogResult indicating whether the pipeline is stale."""
    if not policy.is_enabled():
        return WatchdogResult(
            pipeline=policy.pipeline,
            stale=False,
            last_success=None,
            max_silence_minutes=policy.max_silence_minutes,
        )

    threshold = timedelta(minutes=policy.max_silence_minutes)
    cutoff = datetime.utcnow() - threshold

    last_success: Optional[datetime] = None
    for entry in reversed(history.entries):
        if entry.pipeline == policy.pipeline and entry.succeeded():
            last_success = entry.timestamp
            break

    stale = last_success is None or last_success < cutoff
    return WatchdogResult(
        pipeline=policy.pipeline,
        stale=stale,
        last_success=last_success,
        max_silence_minutes=policy.max_silence_minutes,
    )
