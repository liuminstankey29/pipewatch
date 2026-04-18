"""CLI helpers for lockfile arguments."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.lockfile import LockFile, _DEFAULT_DIR


def add_lock_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("concurrency")
    grp.add_argument(
        "--no-lock",
        action="store_true",
        default=False,
        help="Skip lockfile check (allow concurrent runs).",
    )
    grp.add_argument(
        "--lock-dir",
        default=None,
        metavar="DIR",
        help=f"Directory for lockfiles (default: {_DEFAULT_DIR}).",
    )


def lock_from_args(pipeline: str, args: argparse.Namespace) -> LockFile | None:
    """Return a LockFile, or None if locking is disabled."""
    if getattr(args, "no_lock", False):
        return None
    lock_dir = Path(args.lock_dir) if getattr(args, "lock_dir", None) else _DEFAULT_DIR
    return LockFile(pipeline=pipeline, lock_dir=lock_dir)


def lock_from_config(pipeline: str, cfg: dict) -> LockFile | None:
    """Build a LockFile from config dict keys: lock_dir, no_lock."""
    if cfg.get("no_lock", False):
        return None
    lock_dir = Path(cfg["lock_dir"]) if cfg.get("lock_dir") else _DEFAULT_DIR
    return LockFile(pipeline=pipeline, lock_dir=lock_dir)
