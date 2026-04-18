"""Lockfile support to prevent concurrent pipeline runs."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_DEFAULT_DIR = Path.home() / ".pipewatch" / "locks"


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


@dataclass
class LockFile:
    pipeline: str
    lock_dir: Path = _DEFAULT_DIR

    @property
    def path(self) -> Path:
        safe = self.pipeline.replace("/", "_").replace(" ", "_")
        return self.lock_dir / f"{safe}.lock"

    def acquire(self) -> None:
        """Write a lockfile; raise LockError if one already exists."""
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            info = _read(self.path)
            raise LockError(
                f"Pipeline '{self.pipeline}' is already running "
                f"(pid={info.get('pid')}, started={info.get('started')})"
            )
        _write(self.path, {"pid": os.getpid(), "started": time.time(), "pipeline": self.pipeline})

    def release(self) -> None:
        """Remove the lockfile if it exists."""
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    def is_locked(self) -> bool:
        return self.path.exists()

    def info(self) -> Optional[dict]:
        if not self.path.exists():
            return None
        return _read(self.path)

    def __enter__(self) -> "LockFile":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()


def _write(path: Path, data: dict) -> None:
    import json
    path.write_text(json.dumps(data))


def _read(path: Path) -> dict:
    import json
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}
