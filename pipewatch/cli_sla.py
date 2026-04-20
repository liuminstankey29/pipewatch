"""CLI helpers for SLA policy arguments."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.sla import SLAPolicy


def add_sla_args(parser: argparse.ArgumentParser) -> None:
    """Attach SLA-related flags to an argument parser."""
    g = parser.add_argument_group("SLA")
    g.add_argument(
        "--sla-warn",
        metavar="SECONDS",
        type=float,
        default=None,
        help="Emit a warning if the pipeline exceeds this duration (seconds).",
    )
    g.add_argument(
        "--sla-max",
        metavar="SECONDS",
        type=float,
        default=None,
        help="Treat the run as an SLA breach if it exceeds this duration (seconds).",
    )


def policy_from_args(args: argparse.Namespace, pipeline: str = "") -> SLAPolicy:
    """Build an SLAPolicy from parsed CLI arguments."""
    return SLAPolicy(
        warn_seconds=args.sla_warn,
        max_seconds=args.sla_max,
        pipeline=pipeline,
    )


def policy_from_config(cfg: dict, pipeline: str = "") -> SLAPolicy:
    """Build an SLAPolicy from a config dict (e.g. loaded TOML/JSON)."""
    sla = cfg.get("sla", {})
    return SLAPolicy(
        warn_seconds=sla.get("warn_seconds"),
        max_seconds=sla.get("max_seconds"),
        pipeline=pipeline,
    )


def resolve_sla(
    args: argparse.Namespace,
    cfg: Optional[dict] = None,
    pipeline: str = "",
) -> SLAPolicy:
    """Return a policy from args, falling back to config when args are absent."""
    if args.sla_warn is not None or args.sla_max is not None:
        return policy_from_args(args, pipeline=pipeline)
    if cfg:
        return policy_from_config(cfg, pipeline=pipeline)
    return SLAPolicy(pipeline=pipeline)
