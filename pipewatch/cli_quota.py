"""CLI helpers for quota policy."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.quota import QuotaPolicy


def add_quota_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("quota")
    g.add_argument(
        "--quota-max",
        type=int,
        default=0,
        metavar="N",
        help="max pipeline runs allowed in the quota period (0 = disabled)",
    )
    g.add_argument(
        "--quota-period",
        type=int,
        default=86400,
        metavar="SECONDS",
        help="quota window in seconds (default 86400 = 24 h)",
    )
    g.add_argument(
        "--quota-state-dir",
        default="/tmp/pipewatch/quota",
        metavar="DIR",
        help="directory for quota state files",
    )


def policy_from_args(args: argparse.Namespace) -> QuotaPolicy:
    return QuotaPolicy(
        max_runs=args.quota_max,
        period_seconds=args.quota_period,
        state_dir=args.quota_state_dir,
    )


def policy_from_config(cfg) -> QuotaPolicy:
    raw = getattr(cfg, "quota", {}) or {}
    return QuotaPolicy(
        max_runs=int(raw.get("max_runs", 0)),
        period_seconds=int(raw.get("period_seconds", 86400)),
        state_dir=raw.get("state_dir", "/tmp/pipewatch/quota"),
    )


def resolve_quota(args: argparse.Namespace, cfg) -> QuotaPolicy:
    p = policy_from_config(cfg)
    if args.quota_max:
        p = policy_from_args(args)
    return p
