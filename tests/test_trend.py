"""Tests for pipewatch.trend."""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from pipewatch.history import HistoryEntry
from pipewatch.trend import _linear_slope, analyze_trend, TrendResult


def _entry(duration: float, ok: bool = True) -> HistoryEntry:
    return HistoryEntry(
        pipeline="pipe",
        started_at=datetime.now(timezone.utc).isoformat(),
        exit_code=0 if ok else 1,
        timed_out=False,
        duration_s=duration,
    )


def _history(entries):
    h = MagicMock()
    h.all.return_value = entries
    return h


# --- _linear_slope ---

def test_slope_flat():
    assert _linear_slope([5.0, 5.0, 5.0]) == pytest.approx(0.0)


def test_slope_increasing():
    slope = _linear_slope([1.0, 2.0, 3.0])
    assert slope == pytest.approx(1.0)


def test_slope_decreasing():
    slope = _linear_slope([3.0, 2.0, 1.0])
    assert slope == pytest.approx(-1.0)


def test_slope_single_value():
    assert _linear_slope([42.0]) == 0.0


# --- analyze_trend ---

def test_insufficient_data_fewer_than_3():
    h = _history([_entry(10.0), _entry(12.0)])
    r = analyze_trend(h, "pipe")
    assert r.verdict == "insufficient_data"
    assert r.sample_size == 2


def test_stable_verdict():
    entries = [_entry(10.0) for _ in range(5)]
    h = _history(entries)
    r = analyze_trend(h, "pipe")
    assert r.verdict == "stable"
    assert r.slope == pytest.approx(0.0)


def test_degrading_verdict():
    # slope ~10 s/run => degrading
    entries = [_entry(float(i * 10)) for i in range(1, 6)]
    h = _history(entries)
    r = analyze_trend(h, "pipe", degrade_threshold=5.0)
    assert r.verdict == "degrading"
    assert r.is_degrading()


def test_improving_verdict():
    entries = [_entry(float(50 - i * 10)) for i in range(5)]
    h = _history(entries)
    r = analyze_trend(h, "pipe", improve_threshold=-5.0)
    assert r.verdict == "improving"
    assert not r.is_degrading()


def test_failed_runs_excluded():
    entries = [_entry(10.0), _entry(999.0, ok=False), _entry(10.0), _entry(10.0)]
    h = _history(entries)
    r = analyze_trend(h, "pipe")
    # only 3 successful entries
    assert r.sample_size == 3
    assert r.verdict == "stable"


def test_summary_contains_pipeline_name():
    h = _history([_entry(10.0)] * 5)
    r = analyze_trend(h, "pipe")
    assert "pipe" in r.summary()
    assert r.verdict in r.summary()
