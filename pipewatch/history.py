"""Persistent run history for pipewatch pipelines."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_FILE = Path.home() / ".pipewatch" / "history.json"


@dataclass
class HistoryEntry:
    pipeline: str
    exit_code: int
    timed_out: bool
    duration_seconds: float
    timestamp: str
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class RunHistory:
    def __init__(self, path: Path = DEFAULT_HISTORY_FILE) -> None:
        self.path = Path(path)
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                self._entries = [HistoryEntry.from_dict(e) for e in raw]
            except (json.JSONDecodeError, TypeError):
                self._entries = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(e) for e in self._entries], indent=2))

    def record(self, entry: HistoryEntry) -> None:
        self._entries.append(entry)
        self.save()

    def last(self, n: int = 10) -> List[HistoryEntry]:
        return self._entries[-n:]

    def last_for(self, pipeline: str, n: int = 10) -> List[HistoryEntry]:
        return [e for e in self._entries if e.pipeline == pipeline][-n:]

    def success_rate(self, pipeline: str) -> Optional[float]:
        """Return the success rate (0.0–1.0) for a pipeline, or None if no runs exist."""
        entries = [e for e in self._entries if e.pipeline == pipeline]
        if not entries:
            return None
        return sum(1 for e in entries if e.succeeded) / len(entries)

    def clear(self) -> None:
        self._entries = []
        self.save()
