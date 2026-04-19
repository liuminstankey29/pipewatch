"""CLI helpers for the watchdog feature."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.watchdog import WatchdogPolicy

_DEFAULT_SILENCE = 0  # disabled by default


def add_watchdog_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("watchdog")
    grp.add_argument(
        "--watchdog",
        type=int,
        default=None,
        metavar="MINUTES",
        help="Alert if no successful run within MINUTES (0 = disabled)",
    )


def policy_from_args(args: argparse.Namespace, pipeline: str) -> WatchdogPolicy:
    minutes = getattr(args, "watchdog", None) or _DEFAULT_SILENCE
    return WatchdogPolicy(pipeline=pipeline, max_silence_minutes=minutes)


def policy_from_config(cfg: object, pipeline: str) -> WatchdogPolicy:
    """Build a WatchdogPolicy from a Config object (falls back to disabled)."""
    minutes = getattr(cfg, "watchdog_minutes", None) or _DEFAULT_SILENCE
    return WatchdogPolicy(pipeline=pipeline, max_silence_minutes=int(minutes))


def resolve_watchdog(
    args: argparse.Namespace,
    cfg: object,
    pipeline: str,
) -> WatchdogPolicy:
    """Prefer CLI flag; fall back to config."""
    if getattr(args, "watchdog", None) is not None:
        return policy_from_args(args, pipeline)
    return policy_from_config(cfg, pipeline)
