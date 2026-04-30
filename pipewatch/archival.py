"""Archival policy: move old run logs and history entries to a compressed archive."""
from __future__ import annotations

import gzip
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


@dataclass
class ArchivalPolicy:
    enabled: bool = False
    older_than_days: int = 30
    archive_dir: str = ".pipewatch/archive"
    compress: bool = True

    def is_enabled(self) -> bool:
        return self.enabled and self.older_than_days > 0

    def describe(self) -> str:
        if not self.is_enabled():
            return "archival disabled"
        comp = "compressed" if self.compress else "plain"
        return (
            f"archive entries older than {self.older_than_days}d "
            f"to {self.archive_dir} ({comp})"
        )

    def cutoff(self, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.now(tz=timezone.utc)
        return now - timedelta(days=self.older_than_days)


@dataclass
class ArchivalResult:
    archived: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"archived={self.archived} skipped={self.skipped} "
            f"errors={len(self.errors)}"
        )


def archive_file(src: Path, archive_dir: Path, compress: bool) -> Path:
    """Move *src* into *archive_dir*, optionally gzip-compressing it."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest_name = src.name + (".gz" if compress else "")
    dest = archive_dir / dest_name
    if compress:
        with src.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        src.unlink()
    else:
        shutil.move(str(src), dest)
    return dest


def run_archival(
    policy: ArchivalPolicy,
    log_dir: Path,
    now: Optional[datetime] = None,
) -> ArchivalResult:
    """Scan *log_dir* for JSON run-log files older than the policy cutoff and archive them."""
    result = ArchivalResult()
    if not policy.is_enabled():
        log.debug("archival disabled, skipping")
        return result

    cutoff = policy.cutoff(now)
    archive_dir = Path(policy.archive_dir)

    for path in sorted(log_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            ts_str = data.get("started_at") or data.get("timestamp")
            if not ts_str:
                result.skipped += 1
                continue
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                result.skipped += 1
                continue
            dest = archive_file(path, archive_dir, policy.compress)
            log.info("archived %s -> %s", path, dest)
            result.archived += 1
        except Exception as exc:  # noqa: BLE001
            msg = f"{path}: {exc}"
            log.warning("archival error: %s", msg)
            result.errors.append(msg)
            result.skipped += 1

    return result
