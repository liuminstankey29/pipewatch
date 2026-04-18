"""Simple cron-style schedule checker for pipewatch pipelines."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


_FIELD_NAMES = ("minute", "hour", "dom", "month", "dow")


@dataclass
class Schedule:
    expression: str
    _fields: tuple = ()

    def __post_init__(self) -> None:
        self._fields = _parse(self.expression)

    def is_due(self, at: Optional[datetime] = None) -> bool:
        """Return True if *at* (default: now) matches this schedule."""
        now = at or datetime.now()
        values = (now.minute, now.hour, now.day, now.month, now.weekday())
        return all(_matches(f, v) for f, v in zip(self._fields, values))

    def next_description(self) -> str:
        """Human-readable summary of the expression."""
        return f"cron({self.expression})"


def _parse(expression: str) -> tuple:
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5 cron fields, got {len(parts)}: {expression!r}")
    return tuple(parts)


def _matches(field: str, value: int) -> bool:
    if field == "*":
        return True
    if re.fullmatch(r"\d+", field):
        return int(field) == value
    if re.fullmatch(r"\*/\d+", field):
        step = int(field.split("/")[1])
        return value % step == 0
    if re.fullmatch(r"\d+-\d+", field):
        lo, hi = map(int, field.split("-"))
        return lo <= value <= hi
    if "," in field:
        return any(_matches(f.strip(), value) for f in field.split(","))
    raise ValueError(f"Unsupported cron field: {field!r}")


def from_config(cfg_schedule: str) -> Schedule:
    """Build a Schedule from a config string."""
    return Schedule(expression=cfg_schedule)
