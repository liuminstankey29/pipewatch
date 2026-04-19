"""CLI helpers for cascade suppression policy."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.cascade import CascadePolicy
from pipewatch.config import Config


def add_cascade_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--upstream",
        metavar="PIPELINE",
        action="append",
        default=[],
        help="Upstream pipeline name to watch (repeatable)",
    )
    parser.add_argument(
        "--cascade-window",
        type=int,
        default=30,
        metavar="MINUTES",
        help="Window in minutes to look back for upstream failures (default: 30)",
    )
    parser.add_argument(
        "--cascade-state-dir",
        default=".pipewatch",
        metavar="DIR",
        help="Directory for state files",
    )


def policy_from_args(args: argparse.Namespace) -> CascadePolicy:
    return CascadePolicy(
        upstream=args.upstream or [],
        window_minutes=args.cascade_window,
        state_dir=args.cascade_state_dir,
    )


def policy_from_config(cfg: Config) -> CascadePolicy:
    raw = getattr(cfg, "cascade", {}) or {}
    return CascadePolicy(
        upstream=raw.get("upstream", []),
        window_minutes=int(raw.get("window_minutes", 30)),
        state_dir=raw.get("state_dir", ".pipewatch"),
    )


def resolve_cascade(args: argparse.Namespace, cfg: Optional[Config]) -> CascadePolicy:
    if args.upstream:
        return policy_from_args(args)
    if cfg is not None:
        return policy_from_config(cfg)
    return CascadePolicy()
