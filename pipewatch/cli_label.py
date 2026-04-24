"""CLI helpers for pipeline run labels."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.label import LabelSet, filter_from_labels, labels_from_config, parse_labels


def add_label_args(parser: argparse.ArgumentParser) -> None:
    """Add --label and --filter-label flags to *parser*."""
    parser.add_argument(
        "--label",
        metavar="KEY=VALUE",
        action="append",
        dest="labels",
        default=None,
        help="Attach a label to this run (repeatable).",
    )
    parser.add_argument(
        "--filter-label",
        metavar="KEY=VALUE",
        action="append",
        dest="filter_labels",
        default=None,
        help="Filter history/digest by label (repeatable).",
    )


def labels_from_args(args: argparse.Namespace) -> LabelSet:
    """Build a LabelSet from parsed CLI args."""
    return parse_labels(getattr(args, "labels", None))


def filter_from_args(args: argparse.Namespace) -> dict:
    """Build a filter dict from parsed CLI args."""
    return filter_from_labels(getattr(args, "filter_labels", None))


def resolve_labels(args: argparse.Namespace, cfg: Optional[dict] = None) -> LabelSet:
    """Merge CLI labels on top of config labels (CLI wins)."""
    base = labels_from_config((cfg or {}).get("labels"))
    cli = labels_from_args(args)
    merged = {**base.to_dict(), **cli.to_dict()}
    return LabelSet(merged)
