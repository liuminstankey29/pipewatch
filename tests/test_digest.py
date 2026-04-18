"""Tests for pipewatch.digest."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.digest import (
    DigestSummary,
    build_digest,
    format_digest_message,
    send_digest,
)
from pipewatch.history import HistoryEntry, RunHistory


def _entry(pipeline: str, exit_code: int, hours_ago: float = 1.0, duration: float = 5.0) -> HistoryEntry:
    started = (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat()
    return HistoryEntry(
        pipeline=pipeline,
        started_at=started,
        exit_code=exit_code,
        timed_out=False,
        duration=duration,
    )


@pytest.fixture()
def history(tmp_path):
    h = RunHistory(path=tmp_path / "history.json")
    h.record(_entry("etl", 0, hours_ago=2))
    h.record(_entry("etl", 1, hours_ago=1))
    h.record(_entry("etl", 0, hours_ago=0.5))
    h.record(_entry("other", 0, hours_ago=1))
    return h


def test_build_digest_all(history):
    summary = build_digest(history, period_hours=24)
    assert summary.total == 4
    assert summary.successes == 3
    assert summary.failures == 1


def test_build_digest_filtered(history):
    summary = build_digest(history, pipeline="etl", period_hours=24)
    assert summary.total == 3
    assert summary.failures == 1


def test_build_digest_period_excludes_old(history):
    # period=1h should exclude the entry 2h ago
    summary = build_digest(history, pipeline="etl", period_hours=1)
    assert summary.total == 2


def test_avg_duration(history):
    summary = build_digest(history, period_hours=24)
    assert summary.avg_duration == pytest.approx(5.0)


def test_failure_rate_zero():
    s = DigestSummary(pipeline=None, period_hours=24, total=5, successes=5, failures=0, avg_duration=None)
    assert s.failure_rate == 0.0


def test_format_no_failures():
    s = DigestSummary(pipeline="etl", period_hours=24, total=3, successes=3, failures=0, avg_duration=10.0)
    msg = format_digest_message(s)
    assert ":white_check_mark:" in msg
    assert "etl" in msg
    assert "10.0s" in msg


def test_format_with_failures():
    s = DigestSummary(pipeline="etl", period_hours=24, total=3, successes=2, failures=1, avg_duration=None)
    msg = format_digest_message(s)
    assert ":warning:" in msg
    assert "n/a" in msg


def test_send_digest_calls_slack():
    s = DigestSummary(pipeline=None, period_hours=24, total=1, successes=1, failures=0, avg_duration=2.0)
    with patch("pipewatch.digest.send_slack_alert", return_value=True) as mock_send:
        result = send_digest("https://hooks.slack.com/x", s)
    assert result is True
    mock_send.assert_called_once()
