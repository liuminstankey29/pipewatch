"""Escalation policy: re-alert via Slack if a pipeline stays failed for too long."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class EscalationPolicy:
    enabled: bool = False
    # How many seconds a pipeline must remain failed before escalating
    after_seconds: int = 0
    # Maximum number of escalation pings (0 = unlimited)
    max_pings: int = 0
    state_dir: str = "/tmp/pipewatch/escalation"

    def is_enabled(self) -> bool:
        return self.enabled and self.after_seconds > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "escalation disabled"
        limit = f", max {self.max_pings} pings" if self.max_pings else ""
        return f"escalate after {self.after_seconds}s of continued failure{limit}"

    def _state_path(self, pipeline: str) -> Path:
        return Path(self.state_dir) / f"{pipeline}.json"

    def _load(self, pipeline: str) -> dict:
        p = self._state_path(pipeline)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {}

    def _save(self, pipeline: str, state: dict) -> None:
        p = self._state_path(pipeline)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state))

    def record_failure(self, pipeline: str) -> None:
        """Call when a pipeline run fails; records the start of the failure window."""
        state = self._load(pipeline)
        if "first_failed_at" not in state:
            state["first_failed_at"] = time.time()
            state["ping_count"] = 0
        self._save(pipeline, state)

    def clear(self, pipeline: str) -> None:
        """Call when a pipeline succeeds to reset escalation state."""
        p = self._state_path(pipeline)
        if p.exists():
            p.unlink()

    def should_escalate(self, pipeline: str) -> bool:
        """Return True if an escalation alert should be sent right now."""
        if not self.is_enabled():
            return False
        state = self._load(pipeline)
        if "first_failed_at" not in state:
            return False
        elapsed = time.time() - state["first_failed_at"]
        if elapsed < self.after_seconds:
            return False
        if self.max_pings and state.get("ping_count", 0) >= self.max_pings:
            return False
        return True

    def record_ping(self, pipeline: str) -> None:
        """Increment the ping counter after an escalation alert is sent."""
        state = self._load(pipeline)
        state["ping_count"] = state.get("ping_count", 0) + 1
        self._save(pipeline, state)
