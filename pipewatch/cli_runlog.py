"""CLI helpers for run log commands."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.runlog import DEFAULT_LOG_DIR, list_logs


def add_runlog_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR, help="Directory for run logs")
    parser.add_argument("--log-pipeline", default=None, help="Filter logs by pipeline name")
    parser.add_argument("--log-limit", type=int, default=20, help="Max log entries to show")


def print_runlogs(args: argparse.Namespace) -> None:
    entries = list_logs(log_dir=args.log_dir, pipeline=args.log_pipeline)
    entries = entries[-args.log_limit:]
    if not entries:
        print("No run logs found.")
        return
    for e in entries:
        status = "OK" if e.succeeded() else "FAIL"
        tags = ",".join(e.tags) if e.tags else "-"
        print(f"[{status}] {e.pipeline} | {e.started_at} | {e.duration:.1f}s | tags={tags}")


def log_dir_from_config(cfg) -> str:
    return getattr(cfg, "log_dir", DEFAULT_LOG_DIR)
