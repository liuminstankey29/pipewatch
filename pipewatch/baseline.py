"""Baseline duration tracking — flag runs that deviate significantly from historical norms."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from pipewatch.history import RunHistory


@dataclass
class BaselinePolicy:
    enabled: bool = False
    window: int = 20          # last N successful runs to consider
    threshold: float = 2.0   # multiplier above mean to flag as slow

    def is_enabled(self) -> bool:
        return self.enabled and self.window > 0 and self.threshold > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "baseline: disabled"
        return f"baseline: flag if >{self.threshold}x mean of last {self.window} runs"


@dataclass
class BaselineResult:
    flagged: bool
    elapsed: Optional[float]
    mean: Optional[float]
    threshold_value: Optional[float]
    message: str

    def exceeded(self) -> bool:
        return self.flagged


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def check_baseline(
    policy: BaselinePolicy,
    pipeline: str,
    elapsed: Optional[float],
    history: RunHistory,
) -> BaselineResult:
    if not policy.is_enabled() or elapsed is None:
        return BaselineResult(False, elapsed, None, None, "baseline check skipped")

    entries = [
        e for e in history.entries
        if e.pipeline == pipeline and e.succeeded() and e.duration_s is not None
    ]
    entries = entries[-policy.window:]

    if len(entries) < 3:
        return BaselineResult(False, elapsed, None, None, "not enough history for baseline")

    durations = [e.duration_s for e in entries]
    mean = _mean(durations)
    threshold_value = mean * policy.threshold
    flagged = elapsed > threshold_value
    msg = (
        f"run took {elapsed:.1f}s; mean={mean:.1f}s threshold={threshold_value:.1f}s — "
        + ("SLOW" if flagged else "ok")
    )
    return BaselineResult(flagged, elapsed, mean, threshold_value, msg)
