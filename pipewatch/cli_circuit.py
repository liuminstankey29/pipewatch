"""CLI helpers for circuit-breaker configuration."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.circuit import CircuitBreakerPolicy

_DEFAULT_STATE_DIR = "/tmp/pipewatch/circuit"


def add_circuit_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("circuit breaker")
    grp.add_argument(
        "--circuit-max-failures",
        type=int,
        default=0,
        metavar="N",
        help="open circuit after N consecutive failures (0=disabled)",
    )
    grp.add_argument(
        "--circuit-reset",
        type=int,
        default=300,
        metavar="SECONDS",
        help="seconds before attempting a half-open retry (default: 300)",
    )
    grp.add_argument(
        "--circuit-state-dir",
        default=_DEFAULT_STATE_DIR,
        metavar="DIR",
        help=f"directory for circuit-breaker state files (default: {_DEFAULT_STATE_DIR})",
    )


def policy_from_args(args: argparse.Namespace) -> CircuitBreakerPolicy:
    return CircuitBreakerPolicy(
        max_failures=args.circuit_max_failures,
        reset_seconds=args.circuit_reset,
        state_dir=args.circuit_state_dir,
    )


def policy_from_config(cfg: object) -> CircuitBreakerPolicy:
    """Build a CircuitBreakerPolicy from a Config object (falls back to defaults)."""
    raw = getattr(cfg, "circuit", {}) or {}
    return CircuitBreakerPolicy(
        max_failures=int(raw.get("max_failures", 0)),
        reset_seconds=int(raw.get("reset_seconds", 300)),
        state_dir=raw.get("state_dir", _DEFAULT_STATE_DIR),
    )


def resolve_circuit(
    args: argparse.Namespace, cfg: object
) -> CircuitBreakerPolicy:
    """Prefer CLI flags; fall back to config file values."""
    from_cfg = policy_from_config(cfg)
    cli = policy_from_args(args)
    if cli.is_enabled():
        return cli
    return from_cfg
