"""CLI helpers for on-call rotation config."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.oncall import OnCallRotation, rotation_from_config


def add_oncall_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("on-call")
    grp.add_argument(
        "--oncall-mention",
        action="store_true",
        default=False,
        help="Mention the current on-call person in Slack alerts",
    )


def rotation_from_args(
    args: argparse.Namespace,
    cfg: Optional[dict] = None,
) -> Optional[OnCallRotation]:
    """Return rotation only if --oncall-mention is set and config defines entries."""
    if not getattr(args, "oncall_mention", False):
        return None
    if cfg is None:
        return None
    return rotation_from_config(cfg)


def resolve_oncall(
    args: argparse.Namespace,
    cfg: Optional[dict] = None,
) -> Optional[OnCallRotation]:
    """Resolve rotation from args; fall back to config-level oncall block."""
    rotation = rotation_from_args(args, cfg)
    if rotation is not None:
        return rotation
    if cfg and cfg.get("oncall"):
        return rotation_from_config(cfg)
    return None
