"""CLI helpers for the archival feature."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from pipewatch.archival import ArchivalPolicy, ArchivalResult, run_archival


def add_archival_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("archival")
    grp.add_argument(
        "--archive",
        action="store_true",
        default=False,
        help="Enable archival of old run logs.",
    )
    grp.add_argument(
        "--archive-older-than",
        type=int,
        default=30,
        metavar="DAYS",
        help="Archive entries older than N days (default: 30).",
    )
    grp.add_argument(
        "--archive-dir",
        default=".pipewatch/archive",
        metavar="DIR",
        help="Destination directory for archived files.",
    )
    grp.add_argument(
        "--no-compress",
        action="store_true",
        default=False,
        help="Do not gzip-compress archived files.",
    )


def policy_from_args(args: argparse.Namespace) -> ArchivalPolicy:
    return ArchivalPolicy(
        enabled=args.archive,
        older_than_days=args.archive_older_than,
        archive_dir=args.archive_dir,
        compress=not args.no_compress,
    )


def policy_from_config(cfg: Dict[str, Any]) -> ArchivalPolicy:
    section = cfg.get("archival", {})
    return ArchivalPolicy(
        enabled=section.get("enabled", False),
        older_than_days=int(section.get("older_than_days", 30)),
        archive_dir=section.get("archive_dir", ".pipewatch/archive"),
        compress=section.get("compress", True),
    )


def resolve_archival(
    args: argparse.Namespace,
    cfg: Dict[str, Any],
) -> ArchivalPolicy:
    policy = policy_from_config(cfg)
    if args.archive:
        policy = policy_from_args(args)
    return policy


def execute_archival(policy: ArchivalPolicy, log_dir: str) -> ArchivalResult:
    result = run_archival(policy, Path(log_dir))
    print(f"[archival] {result.summary()}")
    for err in result.errors:
        print(f"  [archival] error: {err}")
    return result
