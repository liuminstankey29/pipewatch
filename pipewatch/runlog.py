"""Structured run log: persist per-run JSON logs to a directory."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_LOG_DIR = os.path.expanduser("~/.pipewatch/runlogs")


@dataclass
class RunLog:
    pipeline: str
    started_at: str
    finished_at: str
    exit_code: int
    timed_out: bool
    duration: float
    tags: List[str]
    notes: str = ""

    def succeeded(self) -> bool:
        return not self.timed_out and self.exit_code == 0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "RunLog":
        return RunLog(**d)


def log_path(log_dir: str, pipeline: str, started_at: str) -> Path:
    safe = pipeline.replace("/", "_").replace(" ", "_")
    ts = started_at.replace(":", "-").replace(" ", "T")
    return Path(log_dir) / f"{safe}__{ts}.json"


def save_log(entry: RunLog, log_dir: str = DEFAULT_LOG_DIR) -> Path:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    p = log_path(log_dir, entry.pipeline, entry.started_at)
    p.write_text(json.dumps(entry.to_dict(), indent=2))
    return p


def load_log(path: str) -> RunLog:
    return RunLog.from_dict(json.loads(Path(path).read_text()))


def list_logs(log_dir: str = DEFAULT_LOG_DIR, pipeline: Optional[str] = None) -> List[RunLog]:
    d = Path(log_dir)
    if not d.exists():
        return []
    logs = []
    for f in sorted(d.glob("*.json")):
        try:
            entry = load_log(str(f))
            if pipeline is None or entry.pipeline == pipeline:
                logs.append(entry)
        except Exception:
            pass
    return logs
