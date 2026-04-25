"""Sliding time-window aggregation for pipeline run history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class WindowPolicy:
    """Configuration for a sliding time window."""
    duration_minutes: int = 0          # 0 = disabled
    pipeline: Optional[str] = None     # filter to a specific pipeline

    def is_enabled(self) -> bool:
        return self.duration_minutes > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "window: disabled"
        return f"window: {self.duration_minutes}m"


@dataclass
class WindowStats:
    """Aggregated stats over a sliding window."""
    pipeline: Optional[str]
    duration_minutes: int
    total: int = 0
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    durations_s: List[float] = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.failures / self.total

    @property
    def avg_duration_s(self) -> Optional[float]:
        if not self.durations_s:
            return None
        return sum(self.durations_s) / len(self.durations_s)

    @property
    def p95_duration_s(self) -> Optional[float]:
        if not self.durations_s:
            return None
        sorted_d = sorted(self.durations_s)
        idx = max(0, int(len(sorted_d) * 0.95) - 1)
        return sorted_d[idx]


def compute_window_stats(
    entries: List[HistoryEntry],
    policy: WindowPolicy,
    now: Optional[datetime] = None,
) -> WindowStats:
    """Compute aggregated stats for entries within the sliding window."""
    if now is None:
        now = datetime.utcnow()

    cutoff = now - timedelta(minutes=policy.duration_minutes)
    stats = WindowStats(
        pipeline=policy.pipeline,
        duration_minutes=policy.duration_minutes,
    )

    for entry in entries:
        if policy.pipeline and entry.pipeline != policy.pipeline:
            continue
        if entry.started_at < cutoff:
            continue
        stats.total += 1
        if entry.timed_out:
            stats.timeouts += 1
            stats.failures += 1
        elif entry.exit_code == 0:
            stats.successes += 1
        else:
            stats.failures += 1
        if entry.duration_s is not None:
            stats.durations_s.append(entry.duration_s)

    return stats


def format_window_stats(stats: WindowStats) -> str:
    """Return a human-readable summary of window stats."""
    lines = [
        f"Window ({stats.duration_minutes}m)"
        + (f" — {stats.pipeline}" if stats.pipeline else ""),
        f"  Runs     : {stats.total}",
        f"  Successes: {stats.successes}",
        f"  Failures : {stats.failures} (timeouts: {stats.timeouts})",
        f"  Fail rate: {stats.failure_rate:.1%}",
    ]
    if stats.avg_duration_s is not None:
        lines.append(f"  Avg dur  : {stats.avg_duration_s:.1f}s")
    if stats.p95_duration_s is not None:
        lines.append(f"  p95 dur  : {stats.p95_duration_s:.1f}s")
    return "\n".join(lines)
