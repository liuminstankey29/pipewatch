"""CLI helpers for heartbeat configuration."""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from pipewatch.heartbeat import HeartbeatPolicy

if TYPE_CHECKING:
    from pipewatch.config import Config


def add_heartbeat_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("heartbeat")
    grp.add_argument(
        "--heartbeat-url",
        default="",
        metavar="URL",
        help="URL to ping for liveness (e.g. healthchecks.io ping URL)",
    )
    grp.add_argument(
        "--heartbeat-interval",
        type=int,
        default=0,
        metavar="SECONDS",
        help="How often to send heartbeat pings (0 = disabled)",
    )
    grp.add_argument(
        "--heartbeat-timeout",
        type=int,
        default=5,
        metavar="SECONDS",
        help="HTTP timeout for each heartbeat ping",
    )


def policy_from_args(args: argparse.Namespace) -> HeartbeatPolicy:
    return HeartbeatPolicy(
        url=args.heartbeat_url,
        interval_seconds=args.heartbeat_interval,
        timeout_seconds=args.heartbeat_timeout,
    )


def policy_from_config(cfg: "Config") -> HeartbeatPolicy:
    raw = getattr(cfg, "heartbeat", {}) or {}
    return HeartbeatPolicy(
        url=raw.get("url", ""),
        interval_seconds=int(raw.get("interval_seconds", 0)),
        timeout_seconds=int(raw.get("timeout_seconds", 5)),
    )


def resolve_heartbeat(args: argparse.Namespace, cfg: "Config") -> HeartbeatPolicy:
    """Prefer CLI flags; fall back to config file values."""
    cli = policy_from_args(args)
    if cli.is_enabled():
        return cli
    return policy_from_config(cfg)
