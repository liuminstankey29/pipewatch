"""Circuit breaker policy: open the circuit after N consecutive failures."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CircuitBreakerPolicy:
    max_failures: int = 0          # 0 = disabled
    reset_seconds: int = 300       # seconds before half-open retry
    state_dir: str = "/tmp/pipewatch/circuit"

    def is_enabled(self) -> bool:
        return self.max_failures > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "circuit-breaker disabled"
        return (
            f"circuit-breaker: open after {self.max_failures} consecutive failures, "
            f"reset after {self.reset_seconds}s"
        )

    def _state_path(self, pipeline: str) -> Path:
        return Path(self.state_dir) / f"{pipeline}.json"

    def _load(self, pipeline: str) -> dict:
        p = self._state_path(pipeline)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"failures": 0, "opened_at": None}

    def _save(self, pipeline: str, state: dict) -> None:
        p = self._state_path(pipeline)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state))

    def is_open(self, pipeline: str) -> bool:
        """Return True when the circuit is open and the run should be skipped."""
        if not self.is_enabled():
            return False
        state = self._load(pipeline)
        if state["opened_at"] is None:
            return False
        elapsed = time.time() - state["opened_at"]
        if elapsed >= self.reset_seconds:
            # half-open: allow one attempt through
            return False
        return state["failures"] >= self.max_failures

    def record_failure(self, pipeline: str) -> None:
        if not self.is_enabled():
            return
        state = self._load(pipeline)
        state["failures"] = state.get("failures", 0) + 1
        if state["failures"] >= self.max_failures and state["opened_at"] is None:
            state["opened_at"] = time.time()
        self._save(pipeline, state)

    def record_success(self, pipeline: str) -> None:
        if not self.is_enabled():
            return
        self._save(pipeline, {"failures": 0, "opened_at": None})

    def reset(self, pipeline: str) -> None:
        p = self._state_path(pipeline)
        if p.exists():
            p.unlink()
