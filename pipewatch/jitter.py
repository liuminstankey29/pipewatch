"""Jitter policy: add randomised delay before pipeline execution to avoid thundering-herd."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterPolicy:
    max_seconds: float = 0.0
    seed: Optional[int] = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def is_enabled(self) -> bool:
        return self.max_seconds > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "jitter disabled"
        return f"jitter up to {self.max_seconds}s"

    def delay(self) -> float:
        """Return a random delay in [0, max_seconds]."""
        if not self.is_enabled():
            return 0.0
        return self._rng.uniform(0, self.max_seconds)

    def sleep(self) -> float:
        """Sleep for a random duration and return how long we slept."""
        secs = self.delay()
        if secs > 0:
            time.sleep(secs)
        return secs


def policy_from_config(cfg: dict) -> JitterPolicy:
    jitter = cfg.get("jitter", {})
    if isinstance(jitter, (int, float)):
        return JitterPolicy(max_seconds=float(jitter))
    return JitterPolicy(
        max_seconds=float(jitter.get("max_seconds", 0)),
        seed=jitter.get("seed"),
    )
