"""CLI helpers for the sliding-window feature."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.window import WindowPolicy


def add_window_args(parser: argparse.ArgumentParser) -> None:
    """Attach --window-* flags to *parser*."""
    grp = parser.add_argument_group("sliding window")
    grp.add_argument(
        "--window",
        metavar="MINUTES",
        type=int,
        default=0,
        dest="window_minutes",
        help="Aggregate stats over a sliding window of MINUTES (0 = off).",
    )
    grp.add_argument(
        "--window-pipeline",
        metavar="NAME",
        default=None,
        dest="window_pipeline",
        help="Restrict window stats to a specific pipeline name.",
    )


def policy_from_args(args: argparse.Namespace) -> WindowPolicy:
    """Build a WindowPolicy from parsed CLI args."""
    return WindowPolicy(
        duration_minutes=args.window_minutes,
        pipeline=args.window_pipeline,
    )


def policy_from_config(cfg: object) -> WindowPolicy:
    """Build a WindowPolicy from a Config object (best-effort)."""
    raw = getattr(cfg, "window", None) or {}
    if isinstance(raw, dict):
        return WindowPolicy(
            duration_minutes=int(raw.get("minutes", 0)),
            pipeline=raw.get("pipeline"),
        )
    return WindowPolicy()


def resolve_window(
    args: argparse.Namespace,
    cfg: Optional[object] = None,
) -> WindowPolicy:
    """Prefer CLI args; fall back to config when window is unset."""
    cli_policy = policy_from_args(args)
    if cli_policy.is_enabled():
        return cli_policy
    if cfg is not None:
        return policy_from_config(cfg)
    return WindowPolicy()
