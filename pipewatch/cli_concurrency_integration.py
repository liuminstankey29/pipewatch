"""Integration helpers: acquire/release concurrency slots around a pipeline run."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pipewatch.concurrency import ConcurrencyPolicy

log = logging.getLogger(__name__)


@dataclass
class ConcurrencyOutcome:
    allowed: bool
    active_before: int
    message: str


def check_concurrency(policy: ConcurrencyPolicy) -> ConcurrencyOutcome:
    """Attempt to acquire a slot.  Returns outcome without raising."""
    if not policy.is_enabled():
        return ConcurrencyOutcome(allowed=True, active_before=0, message="concurrency limit disabled")

    active = policy.active_count()
    allowed = policy.acquire()
    if allowed:
        msg = f"slot acquired ({active + 1}/{policy.max_concurrent} active)"
        log.debug("pipewatch concurrency: %s [pipeline=%s]", msg, policy.pipeline)
    else:
        msg = (
            f"blocked — already {active}/{policy.max_concurrent} "
            f"concurrent runs for pipeline '{policy.pipeline}'"
        )
        log.warning("pipewatch concurrency: %s", msg)

    return ConcurrencyOutcome(allowed=allowed, active_before=active, message=msg)


def release_concurrency(policy: ConcurrencyPolicy) -> None:
    """Release a previously acquired slot.  Safe to call even when disabled."""
    if not policy.is_enabled():
        return
    policy.release()
    log.debug(
        "pipewatch concurrency: slot released (pipeline=%s, active=%d)",
        policy.pipeline,
        policy.active_count(),
    )


def concurrency_exit_code(outcome: ConcurrencyOutcome) -> int:
    """Return 0 when allowed, 2 when blocked (distinct from pipeline failure=1)."""
    return 0 if outcome.allowed else 2
