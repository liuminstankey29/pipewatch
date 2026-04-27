"""CLI helpers for the escalation policy."""
from __future__ import annotations

import argparse
from pipewatch.escalation import EscalationPolicy


def add_escalation_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("escalation")
    g.add_argument(
        "--escalate-after",
        type=int,
        default=0,
        metavar="SECONDS",
        help="Re-alert via Slack if pipeline stays failed for this many seconds (0=off)",
    )
    g.add_argument(
        "--escalate-max-pings",
        type=int,
        default=0,
        metavar="N",
        help="Maximum escalation pings per failure window (0=unlimited)",
    )
    g.add_argument(
        "--escalate-state-dir",
        default="/tmp/pipewatch/escalation",
        metavar="DIR",
        help="Directory for escalation state files",
    )


def policy_from_args(args: argparse.Namespace) -> EscalationPolicy:
    after = getattr(args, "escalate_after", 0)
    return EscalationPolicy(
        enabled=after > 0,
        after_seconds=after,
        max_pings=getattr(args, "escalate_max_pings", 0),
        state_dir=getattr(args, "escalate_state_dir", "/tmp/pipewatch/escalation"),
    )


def policy_from_config(cfg: object) -> EscalationPolicy:
    raw = getattr(cfg, "escalation", {}) or {}
    after = int(raw.get("after_seconds", 0))
    return EscalationPolicy(
        enabled=after > 0,
        after_seconds=after,
        max_pings=int(raw.get("max_pings", 0)),
        state_dir=raw.get("state_dir", "/tmp/pipewatch/escalation"),
    )


def resolve_escalation(args: argparse.Namespace, cfg: object) -> EscalationPolicy:
    cli_policy = policy_from_args(args)
    if cli_policy.is_enabled():
        return cli_policy
    return policy_from_config(cfg)
