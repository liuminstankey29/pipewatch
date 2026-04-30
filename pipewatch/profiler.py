"""Runtime profiling policy: track and compare per-pipeline execution time percentiles."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import RunHistory


@dataclass
class ProfilerPolicy:
    enabled: bool = False
    window: int = 20          # number of recent runs to include
    warn_pct: float = 90.0    # warn if latest run exceeds this percentile
    pipeline: str = ""

    def is_enabled(self) -> bool:
        return self.enabled and self.window > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "profiler disabled"
        return (
            f"profiler: window={self.window} runs, "
            f"warn above p{self.warn_pct:.0f}"
        )


@dataclass
class ProfilerResult:
    elapsed: float
    p50: Optional[float]
    p90: Optional[float]
    pct_rank: Optional[float]   # 0-100: where this run sits in the window
    warn: bool = False
    message: str = ""

    def __post_init__(self) -> None:
        if self.warn:
            self.message = (
                f"slow run: {self.elapsed:.1f}s is at "
                f"p{self.pct_rank:.0f} of recent history "
                f"(p50={self.p50:.1f}s, p90={self.p90:.1f}s)"
            )
        else:
            self.message = (
                f"run time {self.elapsed:.1f}s is within normal range"
            )


def _percentile(data: List[float], pct: float) -> float:
    """Return the *pct*-th percentile of *data* (nearest-rank, 1-indexed)."""
    sorted_data = sorted(data)
    idx = max(0, int(len(sorted_data) * pct / 100.0) - 1)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def _pct_rank(data: List[float], value: float) -> float:
    """Return the percentile rank (0-100) of *value* within *data*."""
    below = sum(1 for x in data if x < value)
    return 100.0 * below / len(data)


def evaluate_profiler(
    policy: ProfilerPolicy,
    history: RunHistory,
    elapsed: float,
) -> Optional[ProfilerResult]:
    """Compare *elapsed* against recent history; return a ProfilerResult or None."""
    if not policy.is_enabled():
        return None

    entries = history.last_for(policy.pipeline, limit=policy.window)
    durations: List[float] = [
        e.duration for e in entries if e.duration is not None and e.succeeded
    ]

    if len(durations) < 2:
        return None

    p50 = statistics.median(durations)
    p90 = _percentile(durations, 90.0)
    rank = _pct_rank(durations, elapsed)
    warn = rank >= policy.warn_pct

    return ProfilerResult(
        elapsed=elapsed,
        p50=p50,
        p90=p90,
        pct_rank=rank,
        warn=warn,
    )
