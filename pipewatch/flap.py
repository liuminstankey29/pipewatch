"""Flap detection: alert when a pipeline oscillates between success and failure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import HistoryEntry


@dataclass
class FlapPolicy:
    min_flaps: int = 0          # minimum state changes to be considered flapping
    window: int = 10            # number of recent runs to inspect

    def is_enabled(self) -> bool:
        return self.min_flaps > 0 and self.window > 1

    def describe(self) -> str:
        if not self.is_enabled():
            return "flap detection disabled"
        return (
            f"flap detection: >={self.min_flaps} state changes "
            f"in last {self.window} runs"
        )


@dataclass
class FlapResult:
    flap_count: int
    threshold: int
    window: int
    transitions: List[str] = field(default_factory=list)

    @property
    def is_flapping(self) -> bool:
        return self.flap_count >= self.threshold

    def message(self) -> str:
        if not self.is_flapping:
            return (
            f"stable: {self.flap_count} state change(s) in last {self.window} runs "
            f"(threshold: {self.threshold})"
        )
        seq = " → ".join(self.transitions)
        return (
            f"flapping: {self.flap_count} state change(s) in last {self.window} runs "
            f"— {seq}"
        )


def _state(entry: HistoryEntry) -> str:
    return "ok" if entry.succeeded() else "fail"


def analyze_flap(
    policy: FlapPolicy,
    entries: List[HistoryEntry],
) -> Optional[FlapResult]:
    """Return a FlapResult if the policy is enabled, else None."""
    if not policy.is_enabled():
        return None

    recent = entries[-policy.window :] if len(entries) > policy.window else entries
    if len(recent) < 2:
        return FlapResult(
            flap_count=0,
            threshold=policy.min_flaps,
            window=policy.window,
            transitions=[_state(e) for e in recent],
        )

    states = [_state(e) for e in recent]
    flap_count = sum(1 for a, b in zip(states, states[1:]) if a != b)
    return FlapResult(
        flap_count=flap_count,
        threshold=policy.min_flaps,
        window=policy.window,
        transitions=states,
    )
