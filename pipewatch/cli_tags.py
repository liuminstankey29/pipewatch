"""CLI helpers for tag-related arguments."""
from __future__ import annotations
import argparse
from pipewatch.tags import parse_tags, TagFilter


def add_tag_args(parser: argparse.ArgumentParser) -> None:
    """Attach ``--tags`` and ``--filter-tags`` arguments to *parser*."""
    parser.add_argument(
        "--tags",
        metavar="TAG[,TAG]",
        default=None,
        help="Comma-separated tags to attach to this run.",
    )
    parser.add_argument(
        "--filter-tags",
        metavar="TAG[,TAG]",
        default=None,
        dest="filter_tags",
        help="Only process runs that carry ALL of these tags.",
    )


def tags_from_args(args: argparse.Namespace) -> list[str]:
    """Return the tag list derived from parsed CLI arguments."""
    return parse_tags(getattr(args, "tags", None))


def filter_from_args(args: argparse.Namespace) -> TagFilter:
    """Return a :class:`TagFilter` derived from parsed CLI arguments."""
    required = parse_tags(getattr(args, "filter_tags", None))
    return TagFilter(required=required)
