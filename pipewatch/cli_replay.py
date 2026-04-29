"""CLI helpers for the replay feature."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.replay import ReplayPolicy


def add_replay_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("replay")
    g.add_argument(
        "--replay",
        metavar="SNAPSHOT_ID",
        default=None,
        help="Re-run pipeline using env from a stored snapshot.",
    )
    g.add_argument(
        "--replay-dir",
        metavar="DIR",
        default=".pipewatch/snapshots",
        help="Directory containing snapshot files (default: .pipewatch/snapshots).",
    )
    g.add_argument(
        "--replay-dry-run",
        action="store_true",
        default=False,
        help="Load snapshot env but do not apply it to the subprocess.",
    )


def policy_from_args(args: argparse.Namespace) -> ReplayPolicy:
    snapshot_id: Optional[str] = getattr(args, "replay", None)
    return ReplayPolicy(
        enabled=snapshot_id is not None,
        snapshot_id=snapshot_id,
        snapshot_dir=getattr(args, "replay_dir", ".pipewatch/snapshots"),
        dry_run=getattr(args, "replay_dry_run", False),
    )


def policy_from_config(cfg: dict) -> ReplayPolicy:
    replay_cfg = cfg.get("replay", {})
    snapshot_id = replay_cfg.get("snapshot_id")
    return ReplayPolicy(
        enabled=bool(snapshot_id),
        snapshot_id=snapshot_id,
        snapshot_dir=replay_cfg.get("snapshot_dir", ".pipewatch/snapshots"),
        dry_run=bool(replay_cfg.get("dry_run", False)),
    )


def resolve_replay(args: argparse.Namespace, cfg: dict) -> ReplayPolicy:
    """Prefer CLI args; fall back to config file."""
    cli_policy = policy_from_args(args)
    if cli_policy.is_enabled():
        return cli_policy
    return policy_from_config(cfg)
