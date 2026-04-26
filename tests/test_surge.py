"""Tests for pipewatch.surge and pipewatch.cli_surge."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.surge import SurgePolicy, SurgeResult, check_surge
from pipewatch.cli_surge import add_surge_args, policy_from_args, policy_from_config


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _entry(minutes_ago: float) -> MagicMock:
    ts = (NOW - timedelta(minutes=minutes_ago)).isoformat()
    e = MagicMock()
    e.started_at = ts
    return e


def _history(*entries):
    h = MagicMock()
    h.last_for.return_value = list(entries)
    h.all.return_value = list(entries)
    return h


def _policy(max_runs: int = 3, window: int = 60) -> SurgePolicy:
    return SurgePolicy(max_runs=max_runs, window_minutes=window, pipeline="etl")


# ---------------------------------------------------------------------------
# SurgePolicy unit tests
# ---------------------------------------------------------------------------

class TestSurgePolicy:
    def test_disabled_when_zero(self):
        assert not SurgePolicy(max_runs=0).is_enabled()

    def test_enabled_when_positive(self):
        assert SurgePolicy(max_runs=5, window_minutes=30).is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in SurgePolicy(max_runs=0).describe()

    def test_describe_enabled(self):
        desc = SurgePolicy(max_runs=10, window_minutes=30).describe()
        assert "10" in desc
        assert "30" in desc


# ---------------------------------------------------------------------------
# check_surge tests
# ---------------------------------------------------------------------------

def test_disabled_policy_never_suppresses():
    h = _history(_entry(5), _entry(10), _entry(15))
    result = check_surge(SurgePolicy(max_runs=0), h, now=NOW)
    assert not result.suppressed
    assert result.run_count == 0


def test_below_threshold_not_suppressed():
    h = _history(_entry(10), _entry(20))
    result = check_surge(_policy(max_runs=5), h, pipeline="etl", now=NOW)
    assert not result.suppressed
    assert result.run_count == 2


def test_at_threshold_suppressed():
    h = _history(_entry(5), _entry(15), _entry(25))
    result = check_surge(_policy(max_runs=3), h, pipeline="etl", now=NOW)
    assert result.suppressed
    assert result.run_count == 3


def test_old_entries_excluded():
    # two recent, two outside the 60-minute window
    h = _history(_entry(30), _entry(45), _entry(90), _entry(120))
    result = check_surge(_policy(max_runs=5, window=60), h, pipeline="etl", now=NOW)
    assert not result.suppressed
    assert result.run_count == 2


def test_message_contains_counts():
    h = _history(_entry(5), _entry(10), _entry(15))
    result = check_surge(_policy(max_runs=3), h, pipeline="etl", now=NOW)
    assert "3" in result.message


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*args):
    p = argparse.ArgumentParser()
    add_surge_args(p)
    return p.parse_args(list(args))


def test_defaults():
    ns = _parse()
    assert ns.surge_max == 0
    assert ns.surge_window == 60


def test_surge_max_flag():
    ns = _parse("--surge-max", "10")
    assert ns.surge_max == 10


def test_surge_window_flag():
    ns = _parse("--surge-window", "30")
    assert ns.surge_window == 30


def test_policy_from_args():
    ns = _parse("--surge-max", "5", "--surge-window", "15")
    p = policy_from_args(ns, pipeline="myp")
    assert p.max_runs == 5
    assert p.window_minutes == 15
    assert p.pipeline == "myp"


def test_policy_from_config():
    cfg = MagicMock()
    cfg.surge = {"max_runs": 8, "window_minutes": 45}
    p = policy_from_config(cfg, pipeline="pipe")
    assert p.max_runs == 8
    assert p.window_minutes == 45


def test_policy_from_config_missing_keys():
    cfg = MagicMock()
    cfg.surge = {}
    p = policy_from_config(cfg)
    assert p.max_runs == 0
    assert p.window_minutes == 60
