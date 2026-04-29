"""CLI helpers for shadow mode."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.shadow import ShadowPolicy


def add_shadow_args(parser: argparse.ArgumentParser) -> None:
    """Register shadow-mode flags on *parser*."""
    grp = parser.add_argument_group("shadow mode")
    grp.add_argument(
        "--shadow",
        action="store_true",
        default=False,
        help="Run pipeline in shadow mode (results are logged but not acted upon).",
    )
    grp.add_argument(
        "--shadow-label",
        metavar="LABEL",
        default="shadow",
        help="Label to attach to shadow runs (default: shadow).",
    )


def policy_from_args(args: argparse.Namespace) -> ShadowPolicy:
    return ShadowPolicy(
        enabled=args.shadow,
        label=args.shadow_label,
    )


def policy_from_config(cfg: dict) -> ShadowPolicy:
    shadow_cfg = cfg.get("shadow", {})
    return ShadowPolicy(
        enabled=bool(shadow_cfg.get("enabled", False)),
        label=str(shadow_cfg.get("label", "shadow")),
    )


def resolve_shadow(
    args: argparse.Namespace,
    cfg: Optional[dict] = None,
) -> ShadowPolicy:
    """Return a ShadowPolicy, preferring CLI flags over config file."""
    if args.shadow:
        return policy_from_args(args)
    if cfg:
        return policy_from_config(cfg)
    return ShadowPolicy()
