"""Tests for pipewatch.window and pipewatch.cli_window."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from typing import List

import pytest

from pipewatch.window import (
    WindowPolicy,
    WindowStats,
    compute_window_stats,
    format_window_stats,
)
from pipewatch.cli_window import add_window_args, policy_from_args, resolve_window
from pipewatch.history import HistoryEntry


NOW = datetime(2024, 6, 1, 12, 0, 0)


def _entry(
    pipeline: str = "etl",
    exit_code: int = 0,
    timed_out: bool = False,
    minutes_ago: float = 5.0,
    duration_s: float = 10.0,
) -> HistoryEntry:
    started = NOW - timedelta(minutes=minutes_ago)
    return HistoryEntry(
        pipeline=pipeline,
        exit_code=exit_code,
        timed_out=timed_out,
        started_at=started,
        duration_s=duration_s,
    )


# ---------------------------------------------------------------------------
# WindowPolicy
# ---------------------------------------------------------------------------

def test_disabled_when_zero():
    assert not WindowPolicy(duration_minutes=0).is_enabled()


def test_enabled_when_positive():
    assert WindowPolicy(duration_minutes=30).is_enabled()


def test_describe_disabled():
    assert "disabled" in WindowPolicy().describe()


def test_describe_enabled():
    desc = WindowPolicy(duration_minutes=60).describe()
    assert "60m" in desc


# ---------------------------------------------------------------------------
# compute_window_stats
# ---------------------------------------------------------------------------

def test_empty_entries_returns_zeros():
    policy = WindowPolicy(duration_minutes=60)
    stats = compute_window_stats([], policy, now=NOW)
    assert stats.total == 0
    assert stats.failure_rate == 0.0
    assert stats.avg_duration_s is None


def test_counts_successes_and_failures():
    entries = [
        _entry(exit_code=0, minutes_ago=10),
        _entry(exit_code=1, minutes_ago=20),
        _entry(exit_code=1, minutes_ago=30),
    ]
    policy = WindowPolicy(duration_minutes=60)
    stats = compute_window_stats(entries, policy, now=NOW)
    assert stats.total == 3
    assert stats.successes == 1
    assert stats.failures == 2
    assert pytest.approx(stats.failure_rate, abs=0.01) == 2 / 3


def test_excludes_entries_outside_window():
    entries = [
        _entry(exit_code=0, minutes_ago=10),
        _entry(exit_code=1, minutes_ago=90),   # outside 60-min window
    ]
    policy = WindowPolicy(duration_minutes=60)
    stats = compute_window_stats(entries, policy, now=NOW)
    assert stats.total == 1
    assert stats.successes == 1


def test_filters_by_pipeline():
    entries = [
        _entry(pipeline="etl", exit_code=0, minutes_ago=5),
        _entry(pipeline="ingest", exit_code=1, minutes_ago=5),
    ]
    policy = WindowPolicy(duration_minutes=60, pipeline="etl")
    stats = compute_window_stats(entries, policy, now=NOW)
    assert stats.total == 1
    assert stats.successes == 1


def test_timeout_counted_as_failure():
    entries = [_entry(exit_code=1, timed_out=True, minutes_ago=5)]
    policy = WindowPolicy(duration_minutes=60)
    stats = compute_window_stats(entries, policy, now=NOW)
    assert stats.timeouts == 1
    assert stats.failures == 1


def test_avg_and_p95_duration():
    entries = [_entry(duration_s=float(d), minutes_ago=1) for d in range(1, 11)]
    policy = WindowPolicy(duration_minutes=60)
    stats = compute_window_stats(entries, policy, now=NOW)
    assert stats.avg_duration_s == pytest.approx(5.5)
    assert stats.p95_duration_s == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# format_window_stats
# ---------------------------------------------------------------------------

def test_format_includes_key_fields():
    stats = WindowStats(pipeline="etl", duration_minutes=30, total=5,
                        successes=4, failures=1, timeouts=0,
                        durations_s=[10.0, 20.0])
    text = format_window_stats(stats)
    assert "30m" in text
    assert "etl" in text
    assert "5" in text
    assert "20.0%" in text or "0.2" in text or "20" in text


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(args: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_window_args(p)
    return p.parse_args(args)


def test_defaults():
    ns = _parse([])
    assert ns.window_minutes == 0
    assert ns.window_pipeline is None


def test_window_flag():
    ns = _parse(["--window", "60"])
    assert ns.window_minutes == 60


def test_pipeline_flag():
    ns = _parse(["--window-pipeline", "etl"])
    assert ns.window_pipeline == "etl"


def test_policy_from_args_disabled():
    ns = _parse([])
    policy = policy_from_args(ns)
    assert not policy.is_enabled()


def test_policy_from_args_enabled():
    ns = _parse(["--window", "30", "--window-pipeline", "etl"])
    policy = policy_from_args(ns)
    assert policy.is_enabled()
    assert policy.pipeline == "etl"


def test_resolve_window_prefers_cli():
    ns = _parse(["--window", "15"])
    policy = resolve_window(ns, cfg=None)
    assert policy.duration_minutes == 15


def test_resolve_window_falls_back_to_config():
    class FakeCfg:
        window = {"minutes": 45, "pipeline": "load"}

    ns = _parse([])
    policy = resolve_window(ns, cfg=FakeCfg())
    assert policy.duration_minutes == 45
    assert policy.pipeline == "load"
