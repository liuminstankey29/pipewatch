"""Pipeline maturity scoring — rates a pipeline's reliability based on recent history."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import HistoryEntry, RunHistory


@dataclass
class MaturityResult:
    score: float  # 0.0 – 100.0
    grade: str    # A / B / C / D / F
    sample_size: int
    success_rate: float
    p50_elapsed: Optional[float]
    p95_elapsed: Optional[float]
    message: str = field(init=False)

    def __post_init__(self) -> None:
        self.message = (
            f"Maturity {self.grade} ({self.score:.1f}/100) "
            f"over {self.sample_size} runs — "
            f"{self.success_rate * 100:.1f}% success"
        )


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    sorted_v = sorted(values)
    idx = math.ceil(pct / 100.0 * len(sorted_v)) - 1
    return sorted_v[max(0, idx)]


def score_pipeline(
    history: RunHistory,
    pipeline: str,
    window: int = 30,
) -> MaturityResult:
    """Compute a maturity score for *pipeline* using the last *window* entries."""
    entries: List[HistoryEntry] = history.last_for(pipeline, n=window)
    if not entries:
        return MaturityResult(
            score=0.0,
            grade="F",
            sample_size=0,
            success_rate=0.0,
            p50_elapsed=None,
            p95_elapsed=None,
        )

    successes = sum(1 for e in entries if e.succeeded())
    success_rate = successes / len(entries)

    elapsed_values = [e.elapsed for e in entries if e.elapsed is not None]
    p50 = _percentile(elapsed_values, 50)
    p95 = _percentile(elapsed_values, 95)

    # Score weights: 70 % success rate + 30 % sample confidence
    confidence = min(len(entries) / window, 1.0)
    score = round((success_rate * 70.0) + (confidence * 30.0), 2)

    return MaturityResult(
        score=score,
        grade=_grade(score),
        sample_size=len(entries),
        success_rate=success_rate,
        p50_elapsed=p50,
        p95_elapsed=p95,
    )
