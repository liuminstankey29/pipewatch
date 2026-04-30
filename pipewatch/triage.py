"""Triage module: classify pipeline failures into categories for smarter alerting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Known triage categories
CATEGORY_TIMEOUT = "timeout"
CATEGORY_OOM = "oom"
CATEGORY_DEPENDENCY = "dependency"
CATEGORY_USER_ERROR = "user_error"
CATEGORY_INFRA = "infra"
CATEGORY_UNKNOWN = "unknown"

_OOM_SIGNALS = ["killed", "out of memory", "oom", "memory limit exceeded"]
_DEPENDENCY_SIGNALS = ["connection refused", "no such host", "timeout connecting", "name resolution"]
_USER_ERROR_SIGNALS = ["permission denied", "no such file", "invalid argument", "syntax error"]
_INFRA_SIGNALS = ["disk full", "no space left", "i/o error", "read-only file system"]


@dataclass
class TriageResult:
    category: str
    confidence: float  # 0.0 – 1.0
    signals: List[str] = field(default_factory=list)
    note: Optional[str] = None

    @property
    def is_known(self) -> bool:
        return self.category != CATEGORY_UNKNOWN

    def summary(self) -> str:
        icon = {"timeout": "⏱", "oom": "💥", "dependency": "🔗",
                "user_error": "🚫", "infra": "🖥", "unknown": "❓"}.get(self.category, "❓")
        return f"{icon} [{self.category}] confidence={self.confidence:.0%}"


def _matches(text: str, signals: List[str]) -> List[str]:
    lower = text.lower()
    return [s for s in signals if s in lower]


def triage_failure(
    exit_code: int,
    timed_out: bool,
    stderr: str = "",
    stdout: str = "",
) -> TriageResult:
    """Classify a pipeline failure into a triage category."""
    combined = f"{stdout}\n{stderr}"

    if timed_out:
        return TriageResult(category=CATEGORY_TIMEOUT, confidence=1.0,
                            signals=["timed_out=True"])

    oom_hits = _matches(combined, _OOM_SIGNALS)
    if oom_hits:
        return TriageResult(category=CATEGORY_OOM, confidence=0.9, signals=oom_hits)

    dep_hits = _matches(combined, _DEPENDENCY_SIGNALS)
    if dep_hits:
        return TriageResult(category=CATEGORY_DEPENDENCY, confidence=0.85, signals=dep_hits)

    infra_hits = _matches(combined, _INFRA_SIGNALS)
    if infra_hits:
        return TriageResult(category=CATEGORY_INFRA, confidence=0.85, signals=infra_hits)

    user_hits = _matches(combined, _USER_ERROR_SIGNALS)
    if user_hits:
        return TriageResult(category=CATEGORY_USER_ERROR, confidence=0.8, signals=user_hits)

    return TriageResult(category=CATEGORY_UNKNOWN, confidence=1.0,
                        note=f"exit_code={exit_code}")
