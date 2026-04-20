"""CLI helpers for the output drain feature."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.drain import DrainPolicy

_DEFAULT_LOG_DIR = ".pipewatch/drain"
_DEFAULT_MAX_KB = 64


def add_drain_args(parser: argparse.ArgumentParser) -> None:
    """Attach drain-related flags to *parser*."""
    g = parser.add_argument_group("output drain")
    g.add_argument(
        "--drain",
        action="store_true",
        default=False,
        help="Capture and persist pipeline stdout/stderr.",
    )
    g.add_argument(
        "--drain-dir",
        default=_DEFAULT_LOG_DIR,
        metavar="DIR",
        help="Directory to store drained output (default: %(default)s).",
    )
    g.add_argument(
        "--drain-max-kb",
        type=int,
        default=_DEFAULT_MAX_KB,
        metavar="KB",
        help="Maximum KB to retain per stream (default: %(default)s).",
    )
    g.add_argument(
        "--drain-no-stdout",
        action="store_true",
        default=False,
        help="Do not capture stdout.",
    )
    g.add_argument(
        "--drain-no-stderr",
        action="store_true",
        default=False,
        help="Do not capture stderr.",
    )


def policy_from_args(args: argparse.Namespace) -> DrainPolicy:
    return DrainPolicy(
        enabled=args.drain,
        log_dir=args.drain_dir,
        max_bytes=args.drain_max_kb * 1024,
        capture_stdout=not args.drain_no_stdout,
        capture_stderr=not args.drain_no_stderr,
    )


def policy_from_config(cfg: dict) -> DrainPolicy:
    """Build a DrainPolicy from a pipewatch config dict."""
    d = cfg.get("drain", {})
    if not d:
        return DrainPolicy()
    return DrainPolicy(
        enabled=bool(d.get("enabled", False)),
        log_dir=str(d.get("log_dir", _DEFAULT_LOG_DIR)),
        max_bytes=int(d.get("max_kb", _DEFAULT_MAX_KB)) * 1024,
        capture_stdout=bool(d.get("capture_stdout", True)),
        capture_stderr=bool(d.get("capture_stderr", True)),
    )


def resolve_drain(
    args: argparse.Namespace, cfg: Optional[dict] = None
) -> DrainPolicy:
    """Prefer CLI flags; fall back to config file values."""
    if args.drain:
        return policy_from_args(args)
    if cfg:
        return policy_from_config(cfg)
    return DrainPolicy()
