"""Tests for pipewatch.notify."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import pytest

from pipewatch.config import Config
from pipewatch.history import RunHistory, HistoryEntry
from pipewatch.monitor import RunResult
from pipewatch.notify import _should_alert, _alert_type, notify


def _cfg(webhook: str = "https://hooks.slack.com/test") -> Config:
    return Config(webhook_url=webhook, timeout=60, retries=0)


def _result(exit_code: int = 0, timed_out: bool = False, duration: float = 1.0) -> RunResult:
    return RunResult(exit_code=exit_code, timed_out=timed_out, duration=duration, stdout="", stderr="")


def _last(succeeded: bool) -> HistoryEntry:
    return HistoryEntry(pipeline="p", exit_code=0 if succeeded else 1, timed_out=False, duration=1.0)


class TestShouldAlert:
    def test_no_webhook_returns_false(self):
        cfg = _cfg(webhook="")
        assert _should_alert(_result(exit_code=1), None, cfg) is False

    def test_failure_returns_true(self):
        assert _should_alert(_result(exit_code=1), None, _cfg()) is True

    def test_success_no_history_returns_false(self):
        assert _should_alert(_result(exit_code=0), None, _cfg()) is False

    def test_recovery_returns_true(self):
        assert _should_alert(_result(exit_code=0), _last(succeeded=False), _cfg()) is True

    def test_success_after_success_returns_false(self):
        assert _should_alert(_result(exit_code=0), _last(succeeded=True), _cfg()) is False


class TestAlertType:
    def test_failure(self):
        assert _alert_type(_result(exit_code=1), None) == "failure"

    def test_timeout(self):
        assert _alert_type(_result(exit_code=1, timed_out=True), None) == "timeout"

    def test_recovery(self):
        assert _alert_type(_result(exit_code=0), _last(succeeded=False)) == "recovery"


class TestNotify:
    @pytest.fixture()
    def history(self, tmp_path):
        return RunHistory(path=tmp_path / "history.json")

    def test_records_entry(self, history):
        with patch("pipewatch.notify.send_slack_alert"):
            notify("mypipe", _result(), history, _cfg())
        assert history.last_for("mypipe") is not None

    def test_sends_alert_on_failure(self, history):
        with patch("pipewatch.notify.send_slack_alert") as mock_send:
            sent = notify("mypipe", _result(exit_code=1), history, _cfg())
        assert sent is True
        mock_send.assert_called_once()

    def test_no_alert_on_success(self, history):
        with patch("pipewatch.notify.send_slack_alert") as mock_send:
            sent = notify("mypipe", _result(exit_code=0), history, _cfg())
        assert sent is False
        mock_send.assert_not_called()

    def test_alert_on_recovery(self, history):
        # Seed a failed entry
        history.record(HistoryEntry(pipeline="mypipe", exit_code=1, timed_out=False, duration=1.0))
        with patch("pipewatch.notify.send_slack_alert") as mock_send:
            sent = notify("mypipe", _result(exit_code=0), history, _cfg())
        assert sent is True
        mock_send.assert_called_once()
