"""Pipeline dependency checking — verify upstream pipelines succeeded before running."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import RunHistory


@dataclass
class DependencyPolicy:
    upstreams: List[str] = field(default_factory=list)
    history_dir: str = ".pipewatch/history"
    lookback: int = 1  # number of recent runs to check per upstream

    def is_enabled(self) -> bool:
        return len(self.upstreams) > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "dependency: disabled"
        names = ", ".join(self.upstreams)
        return f"dependency: requires [{names}] (last {self.lookback} run(s))"


@dataclass
class DependencyResult:
    passed: bool
    failed_upstreams: List[str] = field(default_factory=list)
    missing_upstreams: List[str] = field(default_factory=list)

    def message(self) -> str:
        parts = []
        if self.missing_upstreams:
            parts.append("no history: " + ", ".join(self.missing_upstreams))
        if self.failed_upstreams:
            parts.append("failed: " + ", ".join(self.failed_upstreams))
        if not parts:
            return "all dependencies satisfied"
        return "dependency check failed — " + "; ".join(parts)


def check_dependencies(policy: DependencyPolicy) -> DependencyResult:
    """Return a DependencyResult indicating whether all upstreams are healthy."""
    if not policy.is_enabled():
        return DependencyResult(passed=True)

    failed: List[str] = []
    missing: List[str] = []

    for name in policy.upstreams:
        try:
            history = RunHistory(policy.history_dir)
            entries = history.last_for(name, limit=policy.lookback)
        except Exception:
            missing.append(name)
            continue

        if not entries:
            missing.append(name)
            continue

        if not all(e.succeeded() for e in entries):
            failed.append(name)

    passed = not failed and not missing
    return DependencyResult(passed=passed, failed_upstreams=failed, missing_upstreams=missing)
