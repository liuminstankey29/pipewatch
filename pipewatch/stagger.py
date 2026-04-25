"""Stagger policy: spread pipeline starts across a time window to avoid thundering herd."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StaggerPolicy:
    """Delay pipeline start by a deterministic offset within *window_seconds*."""

    window_seconds: int = 0
    pipeline: str = ""
    seed: str = ""
    _sleep: object = field(default=time.sleep, repr=False, compare=False)

    def is_enabled(self) -> bool:
        return self.window_seconds > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "stagger: disabled"
        offset = self._offset()
        return f"stagger: {offset:.1f}s offset within {self.window_seconds}s window"

    def _offset(self) -> float:
        """Deterministic offset in [0, window_seconds) based on pipeline name + seed."""
        key = f"{self.pipeline}:{self.seed}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        fraction = int(digest[:8], 16) / 0xFFFFFFFF
        return fraction * self.window_seconds

    def apply(self) -> Optional[float]:
        """Sleep for the computed offset; return seconds slept (or None if disabled)."""
        if not self.is_enabled():
            return None
        delay = self._offset()
        if delay > 0:
            self._sleep(delay)
        return delay


def stagger_from_config(cfg: object) -> StaggerPolicy:
    """Build a StaggerPolicy from a Config object."""
    window = getattr(cfg, "stagger_window", 0) or 0
    pipeline = getattr(cfg, "pipeline", "") or ""
    seed = getattr(cfg, "stagger_seed", "") or ""
    return StaggerPolicy(window_seconds=int(window), pipeline=pipeline, seed=seed)
