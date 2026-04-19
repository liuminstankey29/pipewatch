"""On-call rotation support: resolve who to notify for a given pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class OnCallEntry:
    name: str
    slack_user_id: str  # e.g. "U012AB3CD"


@dataclass
class OnCallRotation:
    entries: List[OnCallEntry] = field(default_factory=list)
    epoch: datetime = field(default_factory=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc))
    period_days: int = 7

    def current(self, now: Optional[datetime] = None) -> Optional[OnCallEntry]:
        if not self.entries:
            return None
        now = now or datetime.now(timezone.utc)
        delta = (now - self.epoch).days
        idx = (delta // self.period_days) % len(self.entries)
        return self.entries[idx]

    def mention(self, now: Optional[datetime] = None) -> str:
        entry = self.current(now)
        if entry is None:
            return ""
        return f"<@{entry.slack_user_id}>"


def rotation_from_config(cfg_dict: dict) -> Optional[OnCallRotation]:
    """Build an OnCallRotation from a config sub-dict, or None if absent."""
    raw = cfg_dict.get("oncall")
    if not raw:
        return None
    entries = [
        OnCallEntry(name=e["name"], slack_user_id=e["slack_user_id"])
        for e in raw.get("entries", [])
    ]
    kwargs: dict = {"entries": entries}
    if "period_days" in raw:
        kwargs["period_days"] = int(raw["period_days"])
    if "epoch" in raw:
        kwargs["epoch"] = datetime.fromisoformat(raw["epoch"]).replace(tzinfo=timezone.utc)
    return OnCallRotation(**kwargs)


def format_oncall_mention(rotation: Optional[OnCallRotation], now: Optional[datetime] = None) -> str:
    if rotation is None:
        return ""
    return rotation.mention(now)
