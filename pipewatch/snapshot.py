"""Pipeline state snapshot: capture and compare run summaries for drift detection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Snapshot:
    pipeline: str
    captured_at: str
    exit_code: int
    elapsed: float
    tags: dict
    extra: dict

    def succeeded(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Snapshot":
        return cls(
            pipeline=d["pipeline"],
            captured_at=d["captured_at"],
            exit_code=d["exit_code"],
            elapsed=d["elapsed"],
            tags=d.get("tags", {}),
            extra=d.get("extra", {}),
        )


@dataclass
class SnapshotDiff:
    exit_code_changed: bool
    elapsed_delta: float  # seconds; positive = slower
    tags_added: dict
    tags_removed: dict

    def has_changes(self) -> bool:
        return (
            self.exit_code_changed
            or abs(self.elapsed_delta) > 0
            or bool(self.tags_added)
            or bool(self.tags_removed)
        )

    def summary(self) -> str:
        parts = []
        if self.exit_code_changed:
            parts.append("exit code changed")
        if self.elapsed_delta > 0:
            parts.append(f"+{self.elapsed_delta:.1f}s slower")
        elif self.elapsed_delta < 0:
            parts.append(f"{self.elapsed_delta:.1f}s faster")
        if self.tags_added:
            parts.append(f"tags added: {self.tags_added}")
        if self.tags_removed:
            parts.append(f"tags removed: {self.tags_removed}")
        return "; ".join(parts) if parts else "no changes"


def _snapshot_path(state_dir: str, pipeline: str) -> str:
    safe = pipeline.replace(os.sep, "_").replace(" ", "_")
    return os.path.join(state_dir, f"{safe}.snapshot.json")


def save_snapshot(snapshot: Snapshot, state_dir: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    path = _snapshot_path(state_dir, snapshot.pipeline)
    with open(path, "w") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(pipeline: str, state_dir: str) -> Optional[Snapshot]:
    path = _snapshot_path(state_dir, pipeline)
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return Snapshot.from_dict(json.load(fh))


def diff_snapshots(old: Snapshot, new: Snapshot) -> SnapshotDiff:
    tags_added = {k: v for k, v in new.tags.items() if k not in old.tags}
    tags_removed = {k: v for k, v in old.tags.items() if k not in new.tags}
    return SnapshotDiff(
        exit_code_changed=old.exit_code != new.exit_code,
        elapsed_delta=round(new.elapsed - old.elapsed, 3),
        tags_added=tags_added,
        tags_removed=tags_removed,
    )


def make_snapshot(
    pipeline: str,
    exit_code: int,
    elapsed: float,
    tags: Optional[dict] = None,
    extra: Optional[dict] = None,
) -> Snapshot:
    return Snapshot(
        pipeline=pipeline,
        captured_at=datetime.now(timezone.utc).isoformat(),
        exit_code=exit_code,
        elapsed=elapsed,
        tags=tags or {},
        extra=extra or {},
    )
