"""Run quota enforcement — limit how many times a pipeline can run in a period."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class QuotaPolicy:
    max_runs: int = 0
    period_seconds: int = 86400  # 24 h
    state_dir: str = "/tmp/pipewatch/quota"

    def is_enabled(self) -> bool:
        return self.max_runs > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "quota disabled"
        hours = self.period_seconds / 3600
        return f"max {self.max_runs} runs per {hours:.0f}h"

    def _state_path(self, pipeline: str) -> Path:
        return Path(self.state_dir) / f"{pipeline}.json"

    def _load(self, pipeline: str) -> List[float]:
        p = self._state_path(pipeline)
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text())
        except Exception:
            return []

    def _save(self, pipeline: str, timestamps: List[float]) -> None:
        p = self._state_path(pipeline)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(timestamps))

    def _prune(self, timestamps: List[float], now: float) -> List[float]:
        cutoff = now - self.period_seconds
        return [t for t in timestamps if t >= cutoff]

    def is_exceeded(self, pipeline: str, now: Optional[float] = None) -> bool:
        if not self.is_enabled():
            return False
        now = now or time.time()
        timestamps = self._prune(self._load(pipeline), now)
        return len(timestamps) >= self.max_runs

    def record(self, pipeline: str, now: Optional[float] = None) -> None:
        now = now or time.time()
        timestamps = self._prune(self._load(pipeline), now)
        timestamps.append(now)
        self._save(pipeline, timestamps)

    def reset(self, pipeline: str) -> None:
        self._state_path(pipeline).unlink(missing_ok=True)
