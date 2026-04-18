"""Runs a pipeline on a schedule, respecting retry policy and history."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.config import Config
from pipewatch.history import RunHistory
from pipewatch.notify import notify
from pipewatch.retry import RetryPolicy, run_with_retry
from pipewatch.schedule import Schedule

log = logging.getLogger(__name__)


@dataclass
class ScheduleRunner:
    config: Config
    schedule: Schedule
    history: RunHistory
    policy: Optional[RetryPolicy] = None
    _tick_seconds: int = 60

    def run_loop(self, max_ticks: int = 0) -> None:
        """Block forever (or *max_ticks* iterations) checking the schedule."""
        ticks = 0
        log.info("Schedule loop started: %s", self.schedule.next_description())
        while True:
            if self.schedule.is_due():
                self._execute()
            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
            time.sleep(self._tick_seconds)

    def _execute(self) -> None:
        log.info("Schedule triggered at %s", datetime.now().isoformat())
        policy = self.policy or RetryPolicy()
        result = run_with_retry(self.config.command, policy)
        last = self.history.last_for(self.config.name)
        self.history.record(self.config.name, result.final)
        notify(self.config, result.final, last)
        status = "succeeded" if result.final.succeeded() else "failed"
        log.info("Pipeline %r %s after %d attempt(s)", self.config.name, status, result.attempts)
