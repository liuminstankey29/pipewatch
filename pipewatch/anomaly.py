"""Anomaly detection for pipeline run durations using z-score analysis.

Compares the current run's elapsed time against recent history to flag
statistically unusual runtimes (either unexpectedly fast or slow).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from pipewatch.history import HistoryEntry


@dataclass
class AnomalyPolicy:
    """Configuration for runtime anomaly detection."""

    enabled: bool = False
    # Minimum number of historical runs required before analysis kicks in.
    min_samples: int = 5
    # Number of standard deviations from the mean to consider anomalous.
    z_threshold: float = 3.0
    # How many recent runs to include in the baseline window.
    window: int = 30

    def is_enabled(self) -> bool:
        return self.enabled and self.min_samples > 0 and self.z_threshold > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "anomaly detection disabled"
        return (
            f"anomaly detection enabled "
            f"(z>{self.z_threshold:.1f}, min_samples={self.min_samples}, "
            f"window={self.window})"
        )


@dataclass
class AnomalyResult:
    """Outcome of an anomaly check for a single run."""

    checked: bool
    anomalous: bool
    z_score: Optional[float]
    mean: Optional[float]
    stddev: Optional[float]
    elapsed: Optional[float]
    reason: str = ""

    def message(self) -> str:
        if not self.checked:
            return self.reason
        if not self.anomalous:
            return (
                f"runtime normal "
                f"(z={self.z_score:.2f}, mean={self.mean:.1f}s ±{self.stddev:.1f}s)"
            )
        direction = "slow" if (self.elapsed or 0) > (self.mean or 0) else "fast"
        return (
            f"anomalous runtime detected: {self.elapsed:.1f}s is unusually {direction} "
            f"(z={self.z_score:.2f}, mean={self.mean:.1f}s ±{self.stddev:.1f}s)"
        )


def _elapsed_samples(entries: Sequence[HistoryEntry]) -> List[float]:
    """Extract non-None elapsed values from history entries."""
    return [
        e.elapsed
        for e in entries
        if e.elapsed is not None and e.elapsed > 0
    ]


def check_anomaly(
    policy: AnomalyPolicy,
    current_elapsed: Optional[float],
    history: Sequence[HistoryEntry],
) -> AnomalyResult:
    """Analyse *current_elapsed* against *history* using the given *policy*.

    Returns an :class:`AnomalyResult` describing whether the runtime is
    statistically anomalous.  When there are insufficient samples, or the
    policy is disabled, ``checked`` will be ``False``.
    """
    _no = lambda reason: AnomalyResult(
        checked=False,
        anomalous=False,
        z_score=None,
        mean=None,
        stddev=None,
        elapsed=current_elapsed,
        reason=reason,
    )

    if not policy.is_enabled():
        return _no("anomaly detection disabled")

    if current_elapsed is None or current_elapsed <= 0:
        return _no("no elapsed time for current run")

    recent = list(history)[-policy.window :]
    samples = _elapsed_samples(recent)

    if len(samples) < policy.min_samples:
        return _no(
            f"insufficient samples: {len(samples)} < {policy.min_samples}"
        )

    mean = statistics.mean(samples)

    if len(samples) < 2:
        return _no("need at least 2 samples to compute stddev")

    stddev = statistics.stdev(samples)

    if stddev == 0.0:
        # All historical runs took exactly the same time; any deviation is notable
        # but we cannot compute a meaningful z-score.
        anomalous = current_elapsed != mean
        z_score = math.inf if anomalous else 0.0
    else:
        z_score = abs(current_elapsed - mean) / stddev
        anomalous = z_score > policy.z_threshold

    return AnomalyResult(
        checked=True,
        anomalous=anomalous,
        z_score=z_score,
        mean=mean,
        stddev=stddev,
        elapsed=current_elapsed,
    )
