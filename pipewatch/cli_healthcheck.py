"""CLI helpers for health-check policy."""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from pipewatch.healthcheck import HealthCheckPolicy

if TYPE_CHECKING:
    from pipewatch.config import Config


def add_healthcheck_args(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("health-check")
    g.add_argument("--healthcheck-url", metavar="URL",
                   help="HTTP URL that must return <400 before running")
    g.add_argument("--healthcheck-host", metavar="HOST",
                   help="TCP host to probe before running")
    g.add_argument("--healthcheck-port", metavar="PORT", type=int,
                   help="TCP port to probe before running")
    g.add_argument("--healthcheck-timeout", metavar="SEC", type=float, default=5.0,
                   help="probe timeout in seconds (default: 5)")
    g.add_argument("--healthcheck-optional", action="store_true",
                   help="warn but do not abort when probe fails")


def policy_from_args(args: argparse.Namespace) -> HealthCheckPolicy:
    return HealthCheckPolicy(
        url=getattr(args, "healthcheck_url", None),
        host=getattr(args, "healthcheck_host", None),
        port=getattr(args, "healthcheck_port", None),
        timeout=getattr(args, "healthcheck_timeout", 5.0),
        required=not getattr(args, "healthcheck_optional", False),
    )


def policy_from_config(cfg: "Config") -> HealthCheckPolicy:
    raw = getattr(cfg, "healthcheck", {}) or {}
    return HealthCheckPolicy(
        url=raw.get("url"),
        host=raw.get("host"),
        port=raw.get("port"),
        timeout=float(raw.get("timeout", 5.0)),
        required=bool(raw.get("required", True)),
    )


def resolve_healthcheck(args: argparse.Namespace, cfg: "Config") -> HealthCheckPolicy:
    p = policy_from_args(args)
    if p.is_enabled():
        return p
    return policy_from_config(cfg)
