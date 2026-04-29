"""CLI helpers for the audit-log sub-command."""
from __future__ import annotations

import argparse
from typing import List

from pipewatch.audit import AuditEvent, load_events, clear_events, _DEFAULT_DIR


def add_audit_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("pipeline", help="Pipeline name to inspect")
    parser.add_argument(
        "--event",
        dest="event_type",
        default=None,
        metavar="TYPE",
        help="Filter by event type (e.g. run_start, alert_sent)",
    )
    parser.add_argument(
        "--log-dir",
        default=_DEFAULT_DIR,
        metavar="DIR",
        help="Directory containing audit logs (default: %(default)s)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        default=False,
        help="Delete the audit log for the pipeline",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=None,
        metavar="N",
        help="Show only the last N events",
    )


def _format_event(ev: AuditEvent) -> str:
    detail = ""
    if ev.detail:
        detail = "  " + "  ".join(f"{k}={v}" for k, v in ev.detail.items())
    return f"[{ev.ts}] {ev.event}{detail}"


def print_audit(args: argparse.Namespace) -> None:
    """Handle the audit sub-command.

    Clears the audit log when ``--clear`` is given, otherwise loads and prints
    events for the specified pipeline, applying optional ``--event`` type
    filtering and ``--tail`` truncation.
    """
    if args.clear:
        clear_events(args.pipeline, log_dir=args.log_dir)
        print(f"Audit log cleared for '{args.pipeline}'.")
        return

    if args.tail is not None and args.tail <= 0:
        raise argparse.ArgumentTypeError("--tail must be a positive integer")

    events = load_events(args.pipeline, log_dir=args.log_dir, event_type=args.event_type)
    if args.tail is not None:
        events = events[-args.tail :]
    if not events:
        print(f"No audit events found for '{args.pipeline}'.")
        return
    for ev in events:
        print(_format_event(ev))
