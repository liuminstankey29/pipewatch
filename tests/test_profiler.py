"""Tests for pipewatch.profiler."""
from __future__ import annotations

import datetime
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from pipewatch.profiler import (
    ProfilerPolicy,
    ProfilerResult,
    _pct_rank,
    _percentile,
    evaluate_profiler,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(duration: float, succeeded: bool = True):
    e = MagicMock()
    e.duration = duration
    e.succeeded = succeeded
    return e


def _history(durations: List[float], succeeded: bool = True):
    h = MagicMock()
    h.last_for.return_value = [_entry(d, succeeded) for d in durations]
    return h


# ---------------------------------------------------------------------------
# ProfilerPolicy
# ---------------------------------------------------------------------------

class TestProfilerPolicy:
    def test_disabled_by_default(self):
        p = ProfilerPolicy()
        assert not p.is_enabled()

    def test_enabled_when_flag_set(self):
        p = ProfilerPolicy(enabled=True, window=10)
        assert p.is_enabled()

    def test_disabled_when_window_zero(self):
        p = ProfilerPolicy(enabled=True, window=0)
        assert not p.is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in ProfilerPolicy().describe()

    def test_describe_enabled(self):
        desc = ProfilerPolicy(enabled=True, window=15, warn_pct=95).describe()
        assert "window=15" in desc
        assert "p95" in desc


# ---------------------------------------------------------------------------
# helpers: _percentile, _pct_rank
# ---------------------------------------------------------------------------

def test_percentile_p50():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile(data, 50.0) == 2.0


def test_percentile_p100():
    data = [1.0, 2.0, 3.0]
    assert _percentile(data, 100.0) == 3.0


def test_pct_rank_all_below():
    data = [1.0, 2.0, 3.0, 4.0]
    assert _pct_rank(data, 5.0) == 100.0


def test_pct_rank_none_below():
    data = [2.0, 3.0, 4.0]
    assert _pct_rank(data, 1.0) == 0.0


# ---------------------------------------------------------------------------
# evaluate_profiler
# ---------------------------------------------------------------------------

def test_returns_none_when_disabled():
    policy = ProfilerPolicy(enabled=False)
    h = _history([1.0, 2.0, 3.0])
    assert evaluate_profiler(policy, h, 10.0) is None


def test_returns_none_when_too_few_entries():
    policy = ProfilerPolicy(enabled=True, window=20, pipeline="p")
    h = _history([5.0])  # only one entry
    assert evaluate_profiler(policy, h, 5.0) is None


def test_no_warn_for_fast_run():
    policy = ProfilerPolicy(enabled=True, window=20, warn_pct=90.0, pipeline="p")
    durations = [10.0] * 19
    h = _history(durations)
    result = evaluate_profiler(policy, h, 5.0)
    assert result is not None
    assert not result.warn


def test_warn_for_slow_run():
    policy = ProfilerPolicy(enabled=True, window=20, warn_pct=90.0, pipeline="p")
    durations = list(range(1, 20))  # 1..19
    h = _history(durations)
    result = evaluate_profiler(policy, h, 100.0)  # clearly an outlier
    assert result is not None
    assert result.warn
    assert "slow run" in result.message


def test_failed_entries_excluded():
    """Failed runs should not pollute the baseline."""
    policy = ProfilerPolicy(enabled=True, window=20, warn_pct=90.0, pipeline="p")
    h = MagicMock()
    entries = [_entry(d, succeeded=True) for d in range(1, 10)] + [
        _entry(999.0, succeeded=False)
    ]
    h.last_for.return_value = entries
    result = evaluate_profiler(policy, h, 5.0)
    # 999 should not skew p90 — run of 5 should be unremarkable
    assert result is not None
    assert not result.warn


def test_result_fields_populated():
    policy = ProfilerPolicy(enabled=True, window=20, warn_pct=90.0, pipeline="p")
    durations = [10.0, 20.0, 30.0, 40.0, 50.0]
    h = _history(durations)
    result = evaluate_profiler(policy, h, 35.0)
    assert result.p50 is not None
    assert result.p90 is not None
    assert result.pct_rank is not None
    assert result.elapsed == 35.0
