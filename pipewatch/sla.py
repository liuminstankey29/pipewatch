"""SLA (Service Level Agreement) policy for pipeline duration enforcement."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class SLAPolicy:
    """Defines acceptable duration bounds for a pipeline run."""

    warn_seconds: Optional[float] = None   # alert but don't fail
    max_seconds: Optional[float] = None    # treat as SLA breach
    pipeline: str = ""

    def is_enabled(self) -> bool:
        return bool(self.warn_seconds or self.max_seconds)

    def describe(self) -> str:
        if not self.is_enabled():
            return "SLA: disabled"
        parts = []
        if self.warn_seconds:
            parts.append(f"warn>{self.warn_seconds}s")
        if self.max_seconds:
            parts.append(f"breach>{self.max_seconds}s")
        return "SLA: " + ", ".join(parts)


@dataclass
class SLAResult:
    elapsed: float
    policy: SLAPolicy
    breached: bool = field(init=False)
    warned: bool = field(init=False)

    def __post_init__(self) -> None:
        self.breached = (
            self.policy.max_seconds is not None
            and self.elapsed > self.policy.max_seconds
        )
        self.warned = (
            not self.breached
            and self.policy.warn_seconds is not None
            and self.elapsed > self.policy.warn_seconds
        )

    def message(self) -> str:
        if self.breached:
            return (
                f"SLA breached: pipeline ran {self.elapsed:.1f}s, "
                f"limit {self.policy.max_seconds}s"
            )
        if self.warned:
            return (
                f"SLA warning: pipeline ran {self.elapsed:.1f}s, "
                f"warn threshold {self.policy.warn_seconds}s"
            )
        return f"SLA OK: {self.elapsed:.1f}s"


def check_sla(elapsed: float, policy: SLAPolicy) -> SLAResult:
    """Evaluate elapsed time against the SLA policy."""
    result = SLAResult(elapsed=elapsed, policy=policy)
    if result.breached:
        log.warning(result.message())
    elif result.warned:
        log.info(result.message())
    else:
        log.debug(result.message())
    return result
