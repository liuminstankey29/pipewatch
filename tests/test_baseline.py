"""Tests for pipewatch.baseline."""
from __future__ import annotations
import pytest
from unittest.mock import MagicMock
from pipewatch.baseline import BaselinePolicy, check_baseline
from pipewatch.history import HistoryEntry
from datetime import datetime, timezone


def _entry(pipeline: str, duration: float, success: bool = True) -> HistoryEntry:
    e = MagicMock(spec=HistoryEntry)
    e.pipeline = pipeline
    e.duration_s = duration
    e.succeeded = MagicMock(return_value=success)
    return e


def _history(entries):
    h = MagicMock()
    h.entries = entries
    return h


class TestBaselinePolicy:
    def test_disabled_by_default(self):
        assert not BaselinePolicy().is_enabled()

    def test_enabled_when_flag_set(self):
        assert BaselinePolicy(enabled=True).is_enabled()

    def test_disabled_when_zero_window(self):
        assert not BaselinePolicy(enabled=True, window=0).is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in BaselinePolicy().describe()

    def test_describe_enabled(self):
        d = BaselinePolicy(enabled=True, window=10, threshold=3.0).describe()
        assert "3.0x" in d and "10" in d


class TestCheckBaseline:
    def test_skipped_when_disabled(self):
        policy = BaselinePolicy(enabled=False)
        result = check_baseline(policy, "p", 100.0, _history([]))
        assert not result.flagged
        assert "skipped" in result.message

    def test_skipped_when_no_elapsed(self):
        policy = BaselinePolicy(enabled=True)
        result = check_baseline(policy, "p", None, _history([]))
        assert not result.flagged

    def test_not_enough_history(self):
        policy = BaselinePolicy(enabled=True, window=20)
        h = _history([_entry("p", 10.0), _entry("p", 12.0)])
        result = check_baseline(policy, "p", 50.0, h)
        assert not result.flagged
        assert "not enough" in result.message

    def test_normal_run_not_flagged(self):
        policy = BaselinePolicy(enabled=True, window=10, threshold=2.0)
        entries = [_entry("p", 10.0) for _ in range(5)]
        result = check_baseline(policy, "p", 15.0, _history(entries))
        assert not result.flagged

    def test_slow_run_flagged(self):
        policy = BaselinePolicy(enabled=True, window=10, threshold=2.0)
        entries = [_entry("p", 10.0) for _ in range(5)]
        result = check_baseline(policy, "p", 25.0, _history(entries))
        assert result.flagged
        assert result.mean == pytest.approx(10.0)
        assert result.threshold_value == pytest.approx(20.0)
        assert "SLOW" in result.message

    def test_only_successful_entries_used(self):
        policy = BaselinePolicy(enabled=True, window=20, threshold=2.0)
        entries = [_entry("p", 10.0)] * 4 + [_entry("p", 9999.0, success=False)]
        result = check_baseline(policy, "p", 15.0, _history(entries))
        assert not result.flagged
        assert result.mean == pytest.approx(10.0)

    def test_only_matching_pipeline_used(self):
        policy = BaselinePolicy(enabled=True, window=20, threshold=2.0)
        entries = [_entry("other", 10.0)] * 5 + [_entry("p", 100.0)] * 5
        result = check_baseline(policy, "p", 150.0, _history(entries))
        assert result.mean == pytest.approx(100.0)
