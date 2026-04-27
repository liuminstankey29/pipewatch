"""Suppression policy: skip alerting during a defined maintenance window."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


@dataclass
class SuppressionPolicy:
    """Suppress alerts between *start* and *end* wall-clock times (HH:MM, 24-h)."""

    start: Optional[str] = None   # e.g. "22:00"
    end: Optional[str] = None     # e.g. "06:00"  (may wrap midnight)
    weekdays_only: bool = False   # if True, only suppress on Mon-Fri

    def is_enabled(self) -> bool:
        return bool(self.start and self.end)

    def describe(self) -> str:
        if not self.is_enabled():
            return "suppression disabled"
        suffix = " (weekdays only)" if self.weekdays_only else ""
        return f"suppress alerts {self.start}–{self.end}{suffix}"

    def is_suppressed(self, now: Optional[datetime] = None) -> bool:
        """Return True when *now* falls inside the suppression window."""
        if not self.is_enabled():
            return False
        now = now or datetime.now()
        if self.weekdays_only and now.weekday() >= 5:  # Sat=5, Sun=6
            return False
        t = now.time().replace(second=0, microsecond=0)
        start = _parse_time(self.start)  # type: ignore[arg-type]
        end = _parse_time(self.end)      # type: ignore[arg-type]
        if start <= end:
            return start <= t < end
        # wraps midnight
        return t >= start or t < end


_TIME_RE = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2})$")


def _parse_time(value: str) -> time:
    m = _TIME_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid time format {value!r}; expected HH:MM")
    return time(int(m.group("h")), int(m.group("m")))


def suppression_from_config(cfg: object) -> SuppressionPolicy:
    """Build a SuppressionPolicy from a Config-like object."""
    raw: dict = getattr(cfg, "suppression", {}) or {}
    return SuppressionPolicy(
        start=raw.get("start"),
        end=raw.get("end"),
        weekdays_only=bool(raw.get("weekdays_only", False)),
    )
