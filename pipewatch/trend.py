"""Trend analysis: detect improving/degrading pipeline duration over recent runs."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from pipewatch.history import RunHistory, HistoryEntry


@dataclass
class TrendResult:
    pipeline: str
    sample_size: int
    slope: float          # seconds per run (positive = getting slower)
    mean_duration: float
    verdict: str          # 'improving', 'degrading', 'stable', 'insufficient_data'

    def is_degrading(self) -> bool:
        return self.verdict == "degrading"

    def summary(self) -> str:
        icon = {"improving": "📉", "degrading": "📈", "stable": "➡️", "insufficient_data": "❓"}[self.verdict]
        return (
            f"{icon} {self.pipeline}: {self.verdict} "
            f"(slope={self.slope:+.1f}s/run, mean={self.mean_duration:.1f}s, n={self.sample_size})"
        )


def _linear_slope(values: List[float]) -> float:
    """Return slope of least-squares line through values indexed 0..n-1."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


def analyze_trend(
    history: RunHistory,
    pipeline: str,
    window: int = 10,
    degrade_threshold: float = 5.0,
    improve_threshold: float = -5.0,
) -> TrendResult:
    """Analyse duration trend for *pipeline* over the last *window* successful runs."""
    entries: List[HistoryEntry] = [
        e for e in history.all()
        if e.pipeline == pipeline and e.succeeded() and e.duration_s is not None
    ][-window:]

    if len(entries) < 3:
        return TrendResult(
            pipeline=pipeline,
            sample_size=len(entries),
            slope=0.0,
            mean_duration=0.0,
            verdict="insufficient_data",
        )

    durations = [e.duration_s for e in entries]  # type: ignore[misc]
    slope = _linear_slope(durations)
    mean_dur = sum(durations) / len(durations)

    if slope >= degrade_threshold:
        verdict = "degrading"
    elif slope <= improve_threshold:
        verdict = "improving"
    else:
        verdict = "stable"

    return TrendResult(
        pipeline=pipeline,
        sample_size=len(entries),
        slope=round(slope, 3),
        mean_duration=round(mean_dur, 3),
        verdict=verdict,
    )
