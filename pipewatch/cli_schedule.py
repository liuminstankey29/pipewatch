"""CLI helpers for schedule-related sub-commands."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.config import Config
from pipewatch.retry import RetryPolicy
from pipewatch.schedule import Schedule, from_config


def add_schedule_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--schedule",
        metavar="CRON",
        help="Cron expression (5 fields) to run pipeline on a schedule.",
    )
    parser.add_argument(
        "--tick",
        type=int,
        default=60,
        metavar="SECONDS",
        help="How often (seconds) to check if the schedule is due (default: 60).",
    )


def schedule_from_args(args: argparse.Namespace) -> Optional[Schedule]:
    expr = getattr(args, "schedule", None)
    if not expr:
        return None
    return Schedule(expression=expr)


def schedule_from_config(cfg: Config) -> Optional[Schedule]:
    expr = getattr(cfg, "schedule", None)
    if not expr:
        return None
    return from_config(expr)


def resolve_schedule(args: argparse.Namespace, cfg: Config) -> Optional[Schedule]:
    """CLI args take precedence over config file."""
    return schedule_from_args(args) or schedule_from_config(cfg)
