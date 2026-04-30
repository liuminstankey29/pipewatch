"""CLI helpers for triage: args, config integration, and pretty-printing."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.triage import TriageResult, triage_failure


def add_triage_args(parser: argparse.ArgumentParser) -> None:
    """Add --triage flag to a sub-command parser."""
    grp = parser.add_argument_group("triage")
    grp.add_argument(
        "--triage",
        action="store_true",
        default=False,
        help="Classify failures into triage categories (timeout/oom/dependency/…)",
    )


def triage_from_args(args: argparse.Namespace) -> bool:
    """Return True if triage is enabled via CLI args."""
    return bool(getattr(args, "triage", False))


def triage_from_config(cfg: object) -> bool:
    """Return True if triage is enabled in config dict/object."""
    if isinstance(cfg, dict):
        return bool(cfg.get("triage", False))
    return bool(getattr(cfg, "triage", False))


def resolve_triage(args: argparse.Namespace, cfg: object) -> bool:
    """CLI flag wins; fall back to config."""
    if triage_from_args(args):
        return True
    return triage_from_config(cfg)


def evaluate_and_print(
    exit_code: int,
    timed_out: bool,
    stderr: str = "",
    stdout: str = "",
) -> Optional[TriageResult]:
    """Run triage and print a one-line summary. Returns the result."""
    result = triage_failure(exit_code=exit_code, timed_out=timed_out,
                            stderr=stderr, stdout=stdout)
    print(f"triage: {result.summary()}")
    if result.signals:
        print(f"  signals: {', '.join(result.signals)}")
    if result.note:
        print(f"  note: {result.note}")
    return result
