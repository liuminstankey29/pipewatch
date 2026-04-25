"""Audit log: append-only record of pipeline lifecycle events."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_DEFAULT_DIR = os.path.expanduser("~/.pipewatch/audit")


@dataclass
class AuditEvent:
    pipeline: str
    event: str          # e.g. "run_start", "run_end", "alert_sent", "hook_fired"
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "event": self.event,
            "ts": self.ts,
            "detail": self.detail,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditEvent":
        return AuditEvent(
            pipeline=d["pipeline"],
            event=d["event"],
            ts=d.get("ts", ""),
            detail=d.get("detail", {}),
        )


def _log_path(log_dir: str, pipeline: str) -> Path:
    return Path(log_dir) / f"{pipeline}.audit.jsonl"


def append_event(event: AuditEvent, log_dir: str = _DEFAULT_DIR) -> None:
    """Append *event* to the pipeline's audit log file."""
    path = _log_path(log_dir, event.pipeline)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event.to_dict()) + "\n")


def load_events(
    pipeline: str,
    log_dir: str = _DEFAULT_DIR,
    event_type: Optional[str] = None,
) -> List[AuditEvent]:
    """Return all audit events for *pipeline*, optionally filtered by type."""
    path = _log_path(log_dir, pipeline)
    if not path.exists():
        return []
    events: List[AuditEvent] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = AuditEvent.from_dict(json.loads(line))
            except (json.JSONDecodeError, KeyError):
                continue
            if event_type is None or ev.event == event_type:
                events.append(ev)
    return events


def clear_events(pipeline: str, log_dir: str = _DEFAULT_DIR) -> None:
    """Delete the audit log for *pipeline*."""
    path = _log_path(log_dir, pipeline)
    if path.exists():
        path.unlink()
