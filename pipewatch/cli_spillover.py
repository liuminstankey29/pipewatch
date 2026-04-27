"""CLI helpers for the spillover (duration-overage) policy."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.spillover import SpilloverPolicy


def add_spillover_args(parser: argparse.ArgumentParser) -> None:
    """Attach spillover flags to *parser*."""
    grp = parser.add_argument_group("spillover")
    grp.add_argument(
        "--spillover-warn",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Emit a warning when the run exceeds this many seconds.",
    )
    grp.add_argument(
        "--spillover-max",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Treat the run as a spillover breach above this many seconds.",
    )


def policy_from_args(args: argparse.Namespace) -> SpilloverPolicy:
    return SpilloverPolicy(
        warn_seconds=args.spillover_warn,
        max_seconds=args.spillover_max,
    )


def policy_from_config(cfg: dict) -> SpilloverPolicy:
    spillover = cfg.get("spillover", {})
    return SpilloverPolicy(
        warn_seconds=spillover.get("warn_seconds"),
        max_seconds=spillover.get("max_seconds"),
    )


def resolve_spillover(
    args: argparse.Namespace, cfg: Optional[dict] = None
) -> SpilloverPolicy:
    """Prefer CLI flags; fall back to config dict."""
    if args.spillover_warn is not None or args.spillover_max is not None:
        return policy_from_args(args)
    if cfg:
        return policy_from_config(cfg)
    return SpilloverPolicy()
