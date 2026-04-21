"""Heartbeat policy: periodically send a liveness ping to a URL."""
from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HeartbeatPolicy:
    url: str = ""
    interval_seconds: int = 0  # 0 = disabled
    timeout_seconds: int = 5
    _last_beat: float = field(default=0.0, init=False, repr=False)

    def is_enabled(self) -> bool:
        return bool(self.url) and self.interval_seconds > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "heartbeat disabled"
        return f"heartbeat every {self.interval_seconds}s → {self.url}"

    def is_due(self, now: Optional[float] = None) -> bool:
        if not self.is_enabled():
            return False
        now = now if now is not None else time.monotonic()
        return (now - self._last_beat) >= self.interval_seconds

    def beat(self, now: Optional[float] = None) -> "HeartbeatResult":
        """Send a ping and return the result."""
        if not self.is_enabled():
            return HeartbeatResult(sent=False, status_code=None, error=None)
        try:
            with urllib.request.urlopen(self.url, timeout=self.timeout_seconds) as resp:
                code = resp.status
            self._last_beat = now if now is not None else time.monotonic()
            return HeartbeatResult(sent=True, status_code=code, error=None)
        except Exception as exc:  # noqa: BLE001
            return HeartbeatResult(sent=True, status_code=None, error=str(exc))


@dataclass
class HeartbeatResult:
    sent: bool
    status_code: Optional[int]
    error: Optional[str]

    def succeeded(self) -> bool:
        return self.sent and self.error is None and self.status_code is not None and self.status_code < 400

    def message(self) -> str:
        if not self.sent:
            return "heartbeat skipped (disabled)"
        if self.error:
            return f"heartbeat failed: {self.error}"
        return f"heartbeat ok (HTTP {self.status_code})"
