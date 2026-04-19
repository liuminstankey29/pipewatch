"""CLI helpers for baseline duration policy."""
from __future__ import annotations
import argparse
from pipewatch.baseline import BaselinePolicy
from pipewatch.config import Config


def add_baseline_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("baseline")
    g.add_argument(
        "--baseline",
        action="store_true",
        default=False,
        help="Flag runs that exceed historical duration baseline",
    )
    g.add_argument(
        "--baseline-window",
        type=int,
        default=20,
        metavar="N",
        help="Number of recent successful runs to average (default: 20)",
    )
    g.add_argument(
        "--baseline-threshold",
        type=float,
        default=2.0,
        metavar="X",
        help="Multiplier above mean to trigger flag (default: 2.0)",
    )


def policy_from_args(args: argparse.Namespace) -> BaselinePolicy:
    return BaselinePolicy(
        enabled=args.baseline,
        window=args.baseline_window,
        threshold=args.baseline_threshold,
    )


def policy_from_config(cfg: Config) -> BaselinePolicy:
    raw = getattr(cfg, "baseline", {}) or {}
    return BaselinePolicy(
        enabled=bool(raw.get("enabled", False)),
        window=int(raw.get("window", 20)),
        threshold=float(raw.get("threshold", 2.0)),
    )


def resolve_baseline(args: argparse.Namespace, cfg: Config) -> BaselinePolicy:
    p = policy_from_config(cfg)
    if args.baseline:
        p.enabled = True
    if args.baseline_window != 20:
        p.window = args.baseline_window
    if args.baseline_threshold != 2.0:
        p.threshold = args.baseline_threshold
    return p
