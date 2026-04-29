"""Roster: track which pipelines are registered and their metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class RosterEntry:
    name: str
    description: str = ""
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "RosterEntry":
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            owner=d.get("owner", ""),
            tags=d.get("tags", []),
            enabled=d.get("enabled", True),
        )


@dataclass
class Roster:
    _entries: Dict[str, RosterEntry] = field(default_factory=dict)

    def register(self, entry: RosterEntry) -> None:
        self._entries[entry.name] = entry

    def get(self, name: str) -> Optional[RosterEntry]:
        return self._entries.get(name)

    def all(self) -> List[RosterEntry]:
        return list(self._entries.values())

    def enabled(self) -> List[RosterEntry]:
        return [e for e in self._entries.values() if e.enabled]

    def remove(self, name: str) -> bool:
        if name in self._entries:
            del self._entries[name]
            return True
        return False


def _roster_path(state_dir: str) -> str:
    return os.path.join(state_dir, "roster.json")


def load_roster(state_dir: str) -> Roster:
    path = _roster_path(state_dir)
    if not os.path.exists(path):
        return Roster()
    with open(path) as f:
        data = json.load(f)
    roster = Roster()
    for item in data.get("pipelines", []):
        roster.register(RosterEntry.from_dict(item))
    return roster


def save_roster(roster: Roster, state_dir: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    path = _roster_path(state_dir)
    with open(path, "w") as f:
        json.dump({"pipelines": [e.to_dict() for e in roster.all()]}, f, indent=2)


def format_roster(roster: Roster) -> str:
    entries = roster.all()
    if not entries:
        return "(no pipelines registered)"
    lines = []
    for e in entries:
        status = "enabled" if e.enabled else "disabled"
        tags = ", ".join(e.tags) if e.tags else "-"
        lines.append(f"  {e.name:30s}  [{status:8s}]  owner={e.owner or '-'}  tags={tags}")
        if e.description:
            lines.append(f"    {e.description}")
    return "\n".join(lines)
