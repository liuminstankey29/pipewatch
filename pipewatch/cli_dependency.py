"""CLI helpers for pipeline dependency policy."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.dependency import DependencyPolicy


def add_dependency_args(parser: argparse.ArgumentParser) -> None:
    """Attach dependency-related flags to *parser*."""
    grp = parser.add_argument_group("dependency")
    grp.add_argument(
        "--require",
        metavar="PIPELINE",
        dest="require",
        action="append",
        default=[],
        help="upstream pipeline that must have succeeded (repeatable)",
    )
    grp.add_argument(
        "--dep-lookback",
        metavar="N",
        type=int,
        default=1,
        help="number of recent upstream runs to verify (default: 1)",
    )
    grp.add_argument(
        "--dep-history-dir",
        metavar="DIR",
        default=".pipewatch/history",
        help="history directory to read upstream results from",
    )


def policy_from_args(args: argparse.Namespace) -> DependencyPolicy:
    return DependencyPolicy(
        upstreams=list(args.require),
        lookback=args.dep_lookback,
        history_dir=args.dep_history_dir,
    )


def policy_from_config(cfg: dict) -> DependencyPolicy:
    dep = cfg.get("dependency", {})
    upstreams = dep.get("upstreams", [])
    if isinstance(upstreams, str):
        upstreams = [u.strip() for u in upstreams.split(",") if u.strip()]
    return DependencyPolicy(
        upstreams=upstreams,
        lookback=int(dep.get("lookback", 1)),
        history_dir=dep.get("history_dir", ".pipewatch/history"),
    )


def resolve_dependency(
    args: argparse.Namespace, cfg: Optional[dict] = None
) -> DependencyPolicy:
    """Prefer CLI args; fall back to config file values."""
    if args.require:
        return policy_from_args(args)
    if cfg:
        return policy_from_config(cfg)
    return policy_from_args(args)
