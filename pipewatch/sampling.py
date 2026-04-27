"""Sampling policy — run only a fraction of pipeline executions."""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class SamplingPolicy:
    """Probabilistic sampling: skip execution with probability (1 - rate)."""

    rate: float = 1.0          # 0.0 – 1.0; 1.0 means always run
    seed: int | None = None    # optional RNG seed for deterministic tests
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 <= self.rate <= 1.0):
            raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {self.rate}")
        self._rng = random.Random(self.seed)

    def is_enabled(self) -> bool:
        return self.rate < 1.0

    def describe(self) -> str:
        if not self.is_enabled():
            return "sampling disabled (always run)"
        pct = int(self.rate * 100)
        return f"sampling {pct}% of executions"

    def should_run(self) -> bool:
        """Return True if this execution should proceed."""
        if not self.is_enabled():
            return True
        return self._rng.random() < self.rate


def policy_from_args(args) -> SamplingPolicy:
    rate = getattr(args, "sample_rate", 1.0) or 1.0
    return SamplingPolicy(rate=float(rate))


def policy_from_config(cfg) -> SamplingPolicy:
    rate = float(getattr(cfg, "sample_rate", None) or 1.0)
    return SamplingPolicy(rate=rate)


def resolve_sampling(args, cfg) -> SamplingPolicy:
    """Prefer CLI args; fall back to config."""
    cli_rate = getattr(args, "sample_rate", None)
    if cli_rate is not None:
        return policy_from_args(args)
    return policy_from_config(cfg)
