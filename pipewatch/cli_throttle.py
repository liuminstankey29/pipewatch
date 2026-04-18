"""CLI helpers for throttle policy."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.throttle import ThrottlePolicy


def add_throttle_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--throttle",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Suppress duplicate alerts for the same pipeline within SECONDS (0=off).",
    )
    parser.add_argument(
        "--throttle-state",
        default=None,
        metavar="FILE",
        help="Path to throttle state file (default: .pipewatch_throttle.json).",
    )


def policy_from_args(args: argparse.Namespace) -> ThrottlePolicy:
    kwargs: dict = {"cooldown_seconds": args.throttle}
    state = getattr(args, "throttle_state", None)
    if state:
        kwargs["state_path"] = Path(state)
    return ThrottlePolicy(**kwargs)


def policy_from_config(cfg: dict) -> ThrottlePolicy:
    cooldown = int(cfg.get("throttle_seconds", 0))
    state = cfg.get("throttle_state_path")
    kwargs: dict = {"cooldown_seconds": cooldown}
    if state:
        kwargs["state_path"] = Path(state)
    return ThrottlePolicy(**kwargs)
