"""Tests for pipewatch.cascade and pipewatch.cli_cascade."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.cascade import CascadePolicy, CascadeResult, check_cascade
from pipewatch.cli_cascade import add_cascade_args, policy_from_args, resolve_cascade


def _history(pipeline: str, succeeded: bool, minutes_ago: int = 5):
    entry = MagicMock()
    entry.succeeded.return_value = succeeded
    entry.started_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
    history = MagicMock()
    history.last_for.side_effect = lambda p: entry if p == pipeline else None
    return history


def test_disabled_by_default():
    p = CascadePolicy()
    assert not p.is_enabled()


def test_enabled_with_upstream():
    p = CascadePolicy(upstream=["etl"])
    assert p.is_enabled()


def test_describe_disabled():
    assert "disabled" in CascadePolicy().describe()


def test_describe_enabled():
    p = CascadePolicy(upstream=["etl", "load"], window_minutes=15)
    desc = p.describe()
    assert "15m" in desc
    assert "etl" in desc


def test_no_upstream_not_suppressed():
    result = check_cascade(CascadePolicy(), MagicMock())
    assert not result.suppressed


def test_upstream_succeeded_not_suppressed():
    h = _history("etl", succeeded=True)
    result = check_cascade(CascadePolicy(upstream=["etl"]), h)
    assert not result.suppressed


def test_upstream_failed_recently_suppressed():
    h = _history("etl", succeeded=False, minutes_ago=10)
    result = check_cascade(CascadePolicy(upstream=["etl"], window_minutes=30), h)
    assert result.suppressed
    assert result.upstream_pipeline == "etl"


def test_upstream_failed_outside_window_not_suppressed():
    h = _history("etl", succeeded=False, minutes_ago=60)
    result = check_cascade(CascadePolicy(upstream=["etl"], window_minutes=30), h)
    assert not result.suppressed


def test_unknown_upstream_not_suppressed():
    history = MagicMock()
    history.last_for.return_value = None
    result = check_cascade(CascadePolicy(upstream=["missing"]), history)
    assert not result.suppressed


def test_cascade_result_message_suppressed():
    r = CascadeResult(suppressed=True, upstream_pipeline="etl", failed_at=datetime(2024, 1, 1, 12, 0, 0))
    assert "etl" in r.message()
    assert "2024-01-01" in r.message()


def test_cascade_result_message_not_suppressed():
    r = CascadeResult(suppressed=False)
    assert "no upstream" in r.message()


def _parse(args):
    parser = argparse.ArgumentParser()
    add_cascade_args(parser)
    return parser.parse_args(args)


def test_cli_defaults():
    args = _parse([])
    p = policy_from_args(args)
    assert not p.is_enabled()
    assert p.window_minutes == 30


def test_cli_upstream_flag():
    args = _parse(["--upstream", "etl", "--upstream", "load"])
    p = policy_from_args(args)
    assert p.upstream == ["etl", "load"]


def test_resolve_cascade_prefers_args():
    args = _parse(["--upstream", "etl"])
    p = resolve_cascade(args, cfg=None)
    assert p.upstream == ["etl"]
