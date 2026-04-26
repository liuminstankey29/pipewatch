"""CLI helpers for surge detection."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.surge import SurgePolicy


def add_surge_args(parser: argparse.ArgumentParser) -> None:
    """Add surge-detection flags to *parser*."""
    grp = parser.add_argument_group("surge detection")
    grp.add_argument(
        "--surge-max",
        type=int,
        default=0,
        metavar="N",
        help="suppress run if N or more runs occurred in the window (0=off)",
    )
    grp.add_argument(
        "--surge-window",
        type=int,
        default=60,
        metavar="MINUTES",
        help="rolling window in minutes for surge counting (default: 60)",
    )


def policy_from_args(args: argparse.Namespace, pipeline: str = "") -> SurgePolicy:
    return SurgePolicy(
        max_runs=args.surge_max,
        window_minutes=args.surge_window,
        pipeline=pipeline,
    )


def policy_from_config(cfg, pipeline: str = "") -> SurgePolicy:
    """Build a SurgePolicy from a Config object."""
    raw = getattr(cfg, "surge", {}) or {}
    return SurgePolicy(
        max_runs=int(raw.get("max_runs", 0)),
        window_minutes=int(raw.get("window_minutes", 60)),
        pipeline=pipeline,
    )


def resolve_surge(
    args: argparse.Namespace,
    cfg,
    pipeline: str = "",
    override: Optional[SurgePolicy] = None,
) -> SurgePolicy:
    """Prefer CLI args if --surge-max was explicitly set, else fall back to config."""
    if override is not None:
        return override
    if args.surge_max:
        return policy_from_args(args, pipeline=pipeline)
    return policy_from_config(cfg, pipeline=pipeline)
