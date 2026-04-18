"""Retry logic for pipeline runs."""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from pipewatch.monitor import RunResult

log = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    delay_seconds: float = 5.0
    backoff_factor: float = 2.0
    retry_on_timeout: bool = False

    def delays(self):
        """Yield successive delay values for each retry attempt."""
        d = self.delay_seconds
        for _ in range(self.max_attempts - 1):
            yield d
            d *= self.backoff_factor


@dataclass
class RetryResult:
    final: RunResult
    attempts: int
    history: list[RunResult] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.final.succeeded


def run_with_retry(
    run_fn: Callable[[], RunResult],
    policy: RetryPolicy,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Run *run_fn* up to policy.max_attempts times, retrying on failure."""
    history: list[RunResult] = []
    for attempt in range(1, policy.max_attempts + 1):
        result = run_fn()
        history.append(result)
        if result.succeeded:
            log.info("Pipeline succeeded on attempt %d", attempt)
            return RetryResult(final=result, attempts=attempt, history=history)
        if result.timed_out and not policy.retry_on_timeout:
            log.warning("Pipeline timed out; not retrying (retry_on_timeout=False)")
            return RetryResult(final=result, attempts=attempt, history=history)
        if attempt < policy.max_attempts:
            delay = policy.delay_seconds * (policy.backoff_factor ** (attempt - 1))
            log.warning(
                "Attempt %d/%d failed (exit=%s). Retrying in %.1fs …",
                attempt, policy.max_attempts, result.exit_code, delay,
            )
            sleep_fn(delay)
    log.error("All %d attempts failed.", policy.max_attempts)
    return RetryResult(final=history[-1], attempts=policy.max_attempts, history=history)
