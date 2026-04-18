"""Lightweight runtime metrics collection for pipeline runs."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Metrics:
    pipeline: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    peak_rss_mb: Optional[float] = None
    exit_code: Optional[int] = None
    timed_out: bool = False

    # ------------------------------------------------------------------ #
    @property
    def elapsed(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    def stop(self, exit_code: int, timed_out: bool = False) -> None:
        self.end_time = time.time()
        self.exit_code = exit_code
        self.timed_out = timed_out

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_seconds": round(self.elapsed, 3) if self.elapsed is not None else None,
            "peak_rss_mb": self.peak_rss_mb,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
        }


def capture_rss() -> Optional[float]:
    """Return current process RSS in MB, or None if unavailable."""
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        # Linux returns KB, macOS returns bytes
        import sys
        if sys.platform == "darwin":
            return rss / (1024 * 1024)
        return rss / 1024
    except Exception:
        return None


def collect(pipeline: str) -> Metrics:
    """Start a new Metrics timer for *pipeline*."""
    return Metrics(pipeline=pipeline)


def format_metrics(m: Metrics) -> str:
    parts = [f"pipeline={m.pipeline}"]
    if m.elapsed is not None:
        parts.append(f"elapsed={m.elapsed:.2f}s")
    if m.peak_rss_mb is not None:
        parts.append(f"rss={m.peak_rss_mb:.1f}MB")
    if m.exit_code is not None:
        parts.append(f"exit={m.exit_code}")
    if m.timed_out:
        parts.append("timed_out=true")
    return " ".join(parts)
