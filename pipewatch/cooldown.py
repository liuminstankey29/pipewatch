"""Cooldown policy: suppress pipeline runs within a minimum interval after the last run."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_STATE_DIR = ".pipewatch"


@dataclass
class CooldownPolicy:
    pipeline: str
    seconds: int = 0
    state_dir: str = _DEFAULT_STATE_DIR

    def is_enabled(self) -> bool:
        return self.seconds > 0

    def _state_path(self) -> Path:
        return Path(self.state_dir) / f"cooldown_{self.pipeline}.json"

    def _load(self) -> Optional[float]:
        p = self._state_path()
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text()).get("last_run")
        except (json.JSONDecodeError, OSError):
            return None

    def _save(self) -> None:
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"last_run": time.time()}))

    def is_suppressed(self) -> bool:
        """Return True if the pipeline is still within its cooldown window."""
        if not self.is_enabled():
            return False
        last = self._load()
        if last is None:
            return False
        return (time.time() - last) < self.seconds

    def record(self) -> None:
        """Record that the pipeline ran right now."""
        self._save()

    def remaining(self) -> float:
        """Seconds remaining in the cooldown window (0 if not suppressed)."""
        if not self.is_enabled():
            return 0.0
        last = self._load()
        if last is None:
            return 0.0
        rem = self.seconds - (time.time() - last)
        return max(0.0, rem)

    def reset(self) -> None:
        p = self._state_path()
        if p.exists():
            p.unlink()
