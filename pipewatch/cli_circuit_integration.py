"""Integration helper: apply circuit-breaker logic around a pipeline run.

This module is consumed by cli.py / pipeline_runner.py to skip or allow
a run based on the current circuit state, and to update state afterwards.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from pipewatch.circuit import CircuitBreakerPolicy

log = logging.getLogger(__name__)


@dataclass
class CircuitOutcome:
    skipped: bool = False
    reason: str = ""


def check_circuit(
    policy: CircuitBreakerPolicy, pipeline: str
) -> CircuitOutcome:
    """Return a CircuitOutcome indicating whether the run should be skipped."""
    if not policy.is_enabled():
        return CircuitOutcome(skipped=False)
    if policy.is_open(pipeline):
        reason = (
            f"Circuit is open for '{pipeline}' — "
            f"skipping run (max_failures={policy.max_failures}, "
            f"reset={policy.reset_seconds}s)"
        )
        log.warning(reason)
        return CircuitOutcome(skipped=True, reason=reason)
    return CircuitOutcome(skipped=False)


def update_circuit(
    policy: CircuitBreakerPolicy,
    pipeline: str,
    succeeded: bool,
) -> None:
    """Record the outcome of a completed run into the circuit-breaker state."""
    if not policy.is_enabled():
        return
    if succeeded:
        log.debug("circuit-breaker: recording success for '%s'", pipeline)
        policy.record_success(pipeline)
    else:
        log.debug("circuit-breaker: recording failure for '%s'", pipeline)
        policy.record_failure(pipeline)
        if policy.is_open(pipeline):
            log.warning(
                "circuit-breaker: circuit now OPEN for '%s' after %d consecutive failures",
                pipeline,
                policy.max_failures,
            )
