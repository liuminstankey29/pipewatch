"""Tests for HeartbeatPolicy and HeartbeatResult."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.heartbeat import HeartbeatPolicy, HeartbeatResult


# ---------------------------------------------------------------------------
# HeartbeatPolicy
# ---------------------------------------------------------------------------

class TestHeartbeatPolicy:
    def test_disabled_when_no_url(self):
        p = HeartbeatPolicy(url="", interval_seconds=60)
        assert not p.is_enabled()

    def test_disabled_when_zero_interval(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=0)
        assert not p.is_enabled()

    def test_enabled_when_url_and_interval(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        assert p.is_enabled()

    def test_describe_disabled(self):
        p = HeartbeatPolicy()
        assert "disabled" in p.describe()

    def test_describe_enabled(self):
        p = HeartbeatPolicy(url="http://hc.io/ping/abc", interval_seconds=60)
        desc = p.describe()
        assert "60s" in desc
        assert "hc.io" in desc

    def test_is_due_false_when_disabled(self):
        p = HeartbeatPolicy()
        assert not p.is_due(now=9999.0)

    def test_is_due_true_on_first_call(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        assert p.is_due(now=100.0)

    def test_is_due_false_before_interval(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        p._last_beat = 90.0
        assert not p.is_due(now=100.0)

    def test_is_due_true_after_interval(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        p._last_beat = 60.0
        assert p.is_due(now=100.0)

    def test_beat_disabled_returns_not_sent(self):
        p = HeartbeatPolicy()
        result = p.beat()
        assert not result.sent

    def test_beat_success_updates_last_beat(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = p.beat(now=500.0)
        assert result.succeeded()
        assert result.status_code == 200
        assert p._last_beat == 500.0

    def test_beat_network_error_returns_error(self):
        p = HeartbeatPolicy(url="http://example.com/ping", interval_seconds=30)
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            result = p.beat()
        assert result.sent
        assert not result.succeeded()
        assert "connection refused" in result.error


# ---------------------------------------------------------------------------
# HeartbeatResult
# ---------------------------------------------------------------------------

def test_result_message_skipped():
    r = HeartbeatResult(sent=False, status_code=None, error=None)
    assert "skipped" in r.message()


def test_result_message_ok():
    r = HeartbeatResult(sent=True, status_code=200, error=None)
    assert "ok" in r.message()


def test_result_message_error():
    r = HeartbeatResult(sent=True, status_code=None, error="timeout")
    assert "failed" in r.message()
    assert "timeout" in r.message()


def test_result_not_succeeded_on_4xx():
    r = HeartbeatResult(sent=True, status_code=404, error=None)
    assert not r.succeeded()
