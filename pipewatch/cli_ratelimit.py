"""CLI helpers for rate-limit configuration."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.ratelimit import RateLimitPolicy

_DEFAULT_MAX = 5
_DEFAULT_WINDOW = 3600


def add_ratelimit_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("rate limiting")
    grp.add_argument(
        "--max-alerts",
        type=int,
        default=None,
        metavar="N",
        help="max Slack alerts per window (0 = unlimited)",
    )
    grp.add_argument(
        "--alert-window",
        type=int,
        default=None,
        metavar="SECONDS",
        help="rolling window in seconds for rate limiting",
    )


def policy_from_args(args: argparse.Namespace) -> RateLimitPolicy:
    return RateLimitPolicy(
        max_alerts=args.max_alerts if args.max_alerts is not None else _DEFAULT_MAX,
        window_seconds=args.alert_window if args.alert_window is not None else _DEFAULT_WINDOW,
    )


def policy_from_config(cfg: dict) -> RateLimitPolicy:
    rl = cfg.get("rate_limit", {})
    return RateLimitPolicy(
        max_alerts=int(rl.get("max_alerts", _DEFAULT_MAX)),
        window_seconds=int(rl.get("window_seconds", _DEFAULT_WINDOW)),
        state_file=Path(rl.get("state_file", ".pipewatch_ratelimit.json")),
    )
