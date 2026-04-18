"""CLI helpers for the digest sub-command."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.config import Config


def add_digest_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pipeline",
        default=None,
        help="Filter digest to a specific pipeline name (default: all)",
    )
    parser.add_argument(
        "--period",
        type=int,
        default=24,
        metavar="HOURS",
        help="Look-back window in hours (default: 24)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the digest to Slack (requires webhook in config)",
    )


def period_from_args(args: argparse.Namespace, cfg: Optional[Config] = None) -> int:
    if args.period != 24:
        return args.period
    if cfg and hasattr(cfg, "digest_period_hours") and cfg.digest_period_hours:  # type: ignore[attr-defined]
        return int(cfg.digest_period_hours)  # type: ignore[attr-defined]
    return args.period
