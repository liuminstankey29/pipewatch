"""Helpers that wire RetryPolicy into CLI config and cmd_run."""
from __future__ import annotations

import argparse
from pipewatch.retry import RetryPolicy


def add_retry_args(parser: argparse.ArgumentParser) -> None:
    """Attach retry-related flags to an argparse (sub)parser."""
    g = parser.add_argument_group("retry")
    g.add_argument(
        "--retries",
        type=int,
        default=1,
        metavar="N",
        help="Maximum number of attempts (default: 1 = no retry).",
    )
    g.add_argument(
        "--retry-delay",
        type=float,
        default=5.0,
        metavar="SECS",
        help="Initial delay between retries in seconds (default: 5).",
    )
    g.add_argument(
        "--retry-backoff",
        type=float,
        default=2.0,
        metavar="FACTOR",
        help="Backoff multiplier applied to delay after each retry (default: 2).",
    )
    g.add_argument(
        "--retry-on-timeout",
        action="store_true",
        default=False,
        help="Also retry when the pipeline exceeds its timeout.",
    )


def policy_from_args(args: argparse.Namespace) -> RetryPolicy:
    """Build a RetryPolicy from parsed CLI arguments."""
    return RetryPolicy(
        max_attempts=max(1, args.retries),
        delay_seconds=args.retry_delay,
        backoff_factor=args.retry_backoff,
        retry_on_timeout=args.retry_on_timeout,
    )


def policy_from_config(cfg_dict: dict) -> RetryPolicy:
    """Build a RetryPolicy from a config mapping (e.g. loaded TOML section)."""
    retry = cfg_dict.get("retry", {})
    return RetryPolicy(
        max_attempts=int(retry.get("max_attempts", 1)),
        delay_seconds=float(retry.get("delay_seconds", 5.0)),
        backoff_factor=float(retry.get("backoff_factor", 2.0)),
        retry_on_timeout=bool(retry.get("retry_on_timeout", False)),
    )
