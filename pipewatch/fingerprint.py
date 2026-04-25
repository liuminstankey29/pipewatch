"""Fingerprint: stable hash identifier for a pipeline run's configuration.

Used to detect when a pipeline's command, env, or tags have changed
between runs, which can be surfaced in alerts or history.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Fingerprint:
    """A stable, content-derived identifier for a pipeline invocation."""
    value: str
    components: Dict[str, object] = field(default_factory=dict)

    def short(self, length: int = 8) -> str:
        """Return a short prefix of the hex digest."""
        return self.value[:length]

    def matches(self, other: "Fingerprint") -> bool:
        return self.value == other.value

    def to_dict(self) -> Dict[str, object]:
        return {"value": self.value, "components": self.components}

    @classmethod
    def from_dict(cls, d: Dict[str, object]) -> "Fingerprint":
        return cls(value=str(d["value"]), components=dict(d.get("components", {})))


def compute(
    command: str,
    pipeline: Optional[str] = None,
    tags: Optional[List[str]] = None,
    env_keys: Optional[List[str]] = None,
) -> Fingerprint:
    """Compute a deterministic fingerprint from pipeline invocation metadata.

    Only *keys* of extra env vars are included (not values) to avoid
    capturing secrets in the fingerprint.
    """
    components: Dict[str, object] = {
        "command": command,
        "pipeline": pipeline or "",
        "tags": sorted(tags or []),
        "env_keys": sorted(env_keys or []),
    }
    canonical = json.dumps(components, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return Fingerprint(value=digest, components=components)


def changed(previous: Optional[Fingerprint], current: Fingerprint) -> bool:
    """Return True if the fingerprint has changed since the previous run."""
    if previous is None:
        return False
    return not previous.matches(current)


def describe_change(previous: Fingerprint, current: Fingerprint) -> str:
    """Produce a human-readable summary of what changed between two fingerprints."""
    lines: List[str] = []
    for key in ("command", "pipeline", "tags", "env_keys"):
        old_val = previous.components.get(key)
        new_val = current.components.get(key)
        if old_val != new_val:
            lines.append(f"  {key}: {old_val!r} -> {new_val!r}")
    if not lines:
        return "no differences detected"
    return "\n".join(lines)
