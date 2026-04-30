"""CLI helpers for pipeline version pinning."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.pinning import PinningPolicy


def add_pinning_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("pinning")
    grp.add_argument(
        "--pin",
        action="store_true",
        default=False,
        help="Enable pipeline fingerprint pinning.",
    )
    grp.add_argument(
        "--pin-file",
        default=".pipewatch_pin",
        metavar="PATH",
        help="Path to the pin file (default: .pipewatch_pin).",
    )
    grp.add_argument(
        "--pin-strict",
        action="store_true",
        default=False,
        help="Treat a fingerprint mismatch as a hard error (exit 1).",
    )


def policy_from_args(args: argparse.Namespace) -> PinningPolicy:
    return PinningPolicy(
        enabled=args.pin,
        pin_file=args.pin_file,
        strict=args.pin_strict,
    )


def policy_from_config(cfg: dict) -> PinningPolicy:
    pinning = cfg.get("pinning", {})
    return PinningPolicy(
        enabled=pinning.get("enabled", False),
        pin_file=pinning.get("pin_file", ".pipewatch_pin"),
        strict=pinning.get("strict", False),
    )


def resolve_pinning(
    args: argparse.Namespace,
    cfg: Optional[dict] = None,
) -> PinningPolicy:
    """CLI flags take precedence over config-file settings."""
    base = policy_from_config(cfg or {})
    if args.pin:
        return policy_from_args(args)
    return base
