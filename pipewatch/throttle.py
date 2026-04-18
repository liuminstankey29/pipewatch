"""Alert throttling: suppress duplicate alerts within a cooldown window."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_STATE_FILE = Path(".pipewatch_throttle.json")


@dataclass
class ThrottlePolicy:
    cooldown_seconds: int = 0  # 0 = disabled
    state_path: Path = field(default_factory=lambda: _STATE_FILE)

    def is_enabled(self) -> bool:
        return self.cooldown_seconds > 0

    def _load(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self, state: dict) -> None:
        try:
            self.state_path.write_text(json.dumps(state))
        except OSError:
            pass

    def is_suppressed(self, pipeline: str) -> bool:
        """Return True if an alert for *pipeline* should be suppressed."""
        if not self.is_enabled():
            return False
        state = self._load()
        last = state.get(pipeline)
        if last is None:
            return False
        return (time.time() - last) < self.cooldown_seconds

    def record(self, pipeline: str) -> None:
        """Record that an alert was just sent for *pipeline*."""
        if not self.is_enabled():
            return
        state = self._load()
        state[pipeline] = time.time()
        self._save(state)

    def reset(self, pipeline: Optional[str] = None) -> None:
        """Clear throttle state for one pipeline or all."""
        if pipeline is None:
            self._save({})
        else:
            state = self._load()
            state.pop(pipeline, None)
            self._save(state)
