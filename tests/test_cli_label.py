"""Tests for pipewatch.cli_label."""
from __future__ import annotations

import argparse

import pytest

from pipewatch.cli_label import (
    add_label_args,
    filter_from_args,
    labels_from_args,
    resolve_labels,
)


def _parse(*argv: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_label_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.labels is None
    assert args.filter_labels is None


def test_label_flag_single():
    args = _parse("--label", "env=prod")
    assert args.labels == ["env=prod"]


def test_label_flag_multiple():
    args = _parse("--label", "env=prod", "--label", "team=data")
    assert args.labels == ["env=prod", "team=data"]


def test_filter_label_flag():
    args = _parse("--filter-label", "env=prod")
    assert args.filter_labels == ["env=prod"]


def test_labels_from_args_empty():
    args = _parse()
    ls = labels_from_args(args)
    assert ls.to_dict() == {}


def test_labels_from_args_populated():
    args = _parse("--label", "env=prod")
    ls = labels_from_args(args)
    assert ls.get("env") == "prod"


def test_filter_from_args_empty():
    args = _parse()
    assert filter_from_args(args) == {}


def test_filter_from_args_populated():
    args = _parse("--filter-label", "env=prod")
    assert filter_from_args(args) == {"env": "prod"}


def test_filter_from_args_multiple():
    args = _parse("--filter-label", "env=prod", "--filter-label", "team=data")
    assert filter_from_args(args) == {"env": "prod", "team": "data"}


def test_resolve_labels_cli_wins_over_config():
    args = _parse("--label", "env=staging")
    ls = resolve_labels(args, cfg={"labels": {"env": "prod", "team": "data"}})
    # CLI overrides config for 'env', config value kept for 'team'
    assert ls.get("env") == "staging"
    assert ls.get("team") == "data"


def test_resolve_labels_no_config():
    args = _parse("--label", "env=prod")
    ls = resolve_labels(args)
    assert ls.get("env") == "prod"


def test_resolve_labels_config_only():
    """Config labels are used when no CLI labels are provided."""
    args = _parse()
    ls = resolve_labels(args, cfg={"labels": {"env": "prod", "team": "data"}})
    assert ls.get("env") == "prod"
    assert ls.get("team") == "data"
