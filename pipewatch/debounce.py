"""Debounce policy: suppress alerts until a failure has persisted N consecutive runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_STATE_DIR = os.path.expanduser("~/.pipewatch/debounce")


@dataclass
class DebouncePolicy:
    min_failures: int = 0
    state_dir: str = _DEFAULT_STATE_DIR

    def is_enabled(self) -> bool:
        return self.min_failures > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "debounce disabled"
        return f"alert after {self.min_failures} consecutive failure(s)"

    def _state_path(self, pipeline: str) -> Path:
        return Path(self.state_dir) / f"{pipeline}.json"

    def _load(self, pipeline: str) -> int:
        p = self._state_path(pipeline)
        if p.exists():
            try:
                return int(json.loads(p.read_text()).get("consecutive", 0))
            except Exception:
                return 0
        return 0

    def _save(self, pipeline: str, consecutive: int) -> None:
        p = self._state_path(pipeline)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"consecutive": consecutive}))

    def record_failure(self, pipeline: str) -> int:
        """Increment consecutive failure count and return new value."""
        count = self._load(pipeline) + 1
        self._save(pipeline, count)
        return count

    def record_success(self, pipeline: str) -> None:
        """Reset consecutive failure count on success."""
        self._save(pipeline, 0)

    def is_suppressed(self, pipeline: str) -> bool:
        """Return True if the failure count has NOT yet reached the threshold."""
        if not self.is_enabled():
            return False
        return self._load(pipeline) < self.min_failures

    def reset(self, pipeline: str) -> None:
        self._save(pipeline, 0)
