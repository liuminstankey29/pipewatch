"""Replay policy: re-run a pipeline using a previously recorded snapshot as input context."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ReplayPolicy:
    enabled: bool = False
    snapshot_id: Optional[str] = None
    snapshot_dir: str = ".pipewatch/snapshots"
    dry_run: bool = False

    def is_enabled(self) -> bool:
        return self.enabled and bool(self.snapshot_id)

    def describe(self) -> str:
        if not self.is_enabled():
            return "replay: disabled"
        mode = " (dry-run)" if self.dry_run else ""
        return f"replay: snapshot={self.snapshot_id}{mode}"


@dataclass
class ReplayResult:
    snapshot_id: str
    found: bool
    dry_run: bool
    env_vars: dict = field(default_factory=dict)
    message: str = ""

    def succeeded(self) -> bool:
        return self.found


def load_replay_env(policy: ReplayPolicy) -> ReplayResult:
    """Load environment variables from a stored snapshot for replay."""
    snap_path = Path(policy.snapshot_dir) / f"{policy.snapshot_id}.json"
    if not snap_path.exists():
        log.warning("replay: snapshot not found: %s", snap_path)
        return ReplayResult(
            snapshot_id=policy.snapshot_id,
            found=False,
            dry_run=policy.dry_run,
            message=f"snapshot not found: {snap_path}",
        )

    data = json.loads(snap_path.read_text())
    env_vars = data.get("env", {})
    log.info("replay: loaded %d env vars from %s", len(env_vars), snap_path)
    return ReplayResult(
        snapshot_id=policy.snapshot_id,
        found=True,
        dry_run=policy.dry_run,
        env_vars=env_vars,
        message="ok" if not policy.dry_run else "dry-run: env loaded but not applied",
    )
