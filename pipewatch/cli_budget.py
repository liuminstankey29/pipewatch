"""CLI helpers for budget policy."""
from __future__ import annotations
import argparse
from typing import Optional
from pipewatch.budget import BudgetPolicy


def add_budget_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("budget")
    g.add_argument(
        "--budget-warn",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Warn when pipeline runtime exceeds this many seconds.",
    )
    g.add_argument(
        "--budget-max",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Maximum allowed runtime in seconds.",
    )
    g.add_argument(
        "--budget-hard-fail",
        action="store_true",
        default=False,
        help="Treat budget exceeded as a pipeline failure.",
    )


def policy_from_args(args: argparse.Namespace) -> BudgetPolicy:
    return BudgetPolicy(
        max_seconds=args.budget_max,
        warn_seconds=args.budget_warn,
        hard_fail=args.budget_hard_fail,
    )


def policy_from_config(cfg: object) -> BudgetPolicy:
    raw = getattr(cfg, "budget", {}) or {}
    return BudgetPolicy(
        max_seconds=raw.get("max_seconds"),
        warn_seconds=raw.get("warn_seconds"),
        hard_fail=bool(raw.get("hard_fail", False)),
    )


def resolve_budget(args: argparse.Namespace, cfg: object) -> BudgetPolicy:
    p = policy_from_args(args)
    if p.is_enabled():
        return p
    return policy_from_config(cfg)
