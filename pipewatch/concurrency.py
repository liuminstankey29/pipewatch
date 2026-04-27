"""Concurrency limit policy — prevent more than N simultaneous runs of a pipeline."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_STATE_DIR = "/tmp/pipewatch/concurrency"


@dataclass
class ConcurrencyPolicy:
    max_concurrent: int = 0
    state_dir: str = _DEFAULT_STATE_DIR
    pipeline: str = "default"

    def is_enabled(self) -> bool:
        return self.max_concurrent > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "concurrency limit: disabled"
        return f"concurrency limit: max {self.max_concurrent} simultaneous run(s)"

    def _state_path(self) -> Path:
        return Path(self.state_dir) / f"{self.pipeline}.json"

    def _load(self) -> list[float]:
        p = self._state_path()
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, slots: list[float]) -> None:
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(slots))

    def _prune(self, slots: list[float], ttl: float = 86400.0) -> list[float]:
        cutoff = time.time() - ttl
        return [s for s in slots if s > cutoff]

    def acquire(self) -> bool:
        """Try to acquire a slot. Returns True if allowed, False if at limit."""
        if not self.is_enabled():
            return True
        slots = self._prune(self._load())
        if len(slots) >= self.max_concurrent:
            return False
        slots.append(time.time())
        self._save(slots)
        return True

    def release(self) -> None:
        """Release the oldest acquired slot."""
        slots = self._prune(self._load())
        if slots:
            slots.pop(0)
        self._save(slots)

    def active_count(self) -> int:
        return len(self._prune(self._load()))

    def reset(self) -> None:
        p = self._state_path()
        if p.exists():
            p.unlink()
