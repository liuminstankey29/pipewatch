"""Simple in-memory and file-backed rate limiting for Slack alerts."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_STATE_FILE = Path(".pipewatch_ratelimit.json")


@dataclass
class RateLimitPolicy:
    max_alerts: int = 5          # max alerts per window
    window_seconds: int = 3600   # rolling window in seconds
    state_file: Path = field(default_factory=lambda: _DEFAULT_STATE_FILE)

    def is_enabled(self) -> bool:
        return self.max_alerts > 0 and self.window_seconds > 0


def _load_state(path: Path) -> list[float]:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return []


def _save_state(path: Path, timestamps: list[float]) -> None:
    path.write_text(json.dumps(timestamps))


def _prune(timestamps: list[float], window: int, now: float) -> list[float]:
    cutoff = now - window
    return [t for t in timestamps if t >= cutoff]


def check_and_record(policy: RateLimitPolicy, pipeline: Optional[str] = None) -> bool:
    """Return True if alert is allowed; record the attempt if so."""
    if not policy.is_enabled():
        return True

    suffix = f"_{pipeline}" if pipeline else ""
    path = policy.state_file.parent / (policy.state_file.stem + suffix + policy.state_file.suffix)

    now = time.time()
    timestamps = _prune(_load_state(path), policy.window_seconds, now)

    if len(timestamps) >= policy.max_alerts:
        return False

    timestamps.append(now)
    _save_state(path, timestamps)
    return True


def reset(policy: RateLimitPolicy, pipeline: Optional[str] = None) -> None:
    suffix = f"_{pipeline}" if pipeline else ""
    path = policy.state_file.parent / (policy.state_file.stem + suffix + policy.state_file.suffix)
    if path.exists():
        path.unlink()
