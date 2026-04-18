"""CLI helpers for metrics output flags."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from pipewatch.metrics import Metrics, format_metrics


def add_metrics_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("metrics")
    grp.add_argument(
        "--metrics",
        choices=["none", "text", "json"],
        default="none",
        help="Emit runtime metrics after the run (default: none).",
    )
    grp.add_argument(
        "--metrics-file",
        metavar="PATH",
        default=None,
        help="Write JSON metrics to PATH instead of stdout.",
    )


def emit_metrics(
    m: Metrics,
    mode: str,
    metrics_file: Optional[str] = None,
) -> None:
    """Print or write metrics according to *mode*."""
    if mode == "none":
        return

    if mode == "json":
        payload = json.dumps(m.to_dict(), indent=2)
    else:
        payload = format_metrics(m)

    if metrics_file:
        with open(metrics_file, "w") as fh:
            fh.write(payload + "\n")
    else:
        print(payload, file=sys.stderr)
