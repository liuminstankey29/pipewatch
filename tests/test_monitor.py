"""Tests for pipewatch.monitor."""

import pytest
from unittest.mock import patch, MagicMock

from pipewatch.monitor import run_pipeline, RunResult
from pipewatch.config import Config


def _cfg(**kwargs) -> Config:
    defaults = dict(
        pipeline_name="test-pipe",
        webhook_url="https://hooks.slack.com/test",
        alert_on_slow=False,
        slow_threshold_seconds=None,
    )
    defaults.update(kwargs)
    return Config(**defaults)


class TestRunResult:
    def test_succeeded_true_on_zero_exit(self):
        r = RunResult(command="echo hi", exit_code=0, duration_seconds=0.1)
        assert r.succeeded is True

    def test_succeeded_false_on_nonzero_exit(self):
        r = RunResult(command="false", exit_code=1, duration_seconds=0.1)
        assert r.succeeded is False

    def test_succeeded_false_when_timed_out(self):
        r = RunResult(command="sleep 10", exit_code=0, duration_seconds=5.0, timed_out=True)
        assert r.succeeded is False


class TestRunPipeline:
    def test_successful_command(self):
        result = run_pipeline("echo hello", _cfg())
        assert result.exit_code == 0
        assert result.succeeded
        assert result.duration_seconds >= 0

    def test_failing_command_sends_alert(self):
        cfg = _cfg()
        with patch("pipewatch.monitor.send_slack_alert") as mock_alert:
            result = run_pipeline("exit 1", cfg)
        assert result.exit_code == 1
        mock_alert.assert_called_once()

    def test_successful_command_no_alert(self):
        with patch("pipewatch.monitor.send_slack_alert") as mock_alert:
            run_pipeline("echo ok", _cfg())
        mock_alert.assert_not_called()

    def test_slow_command_triggers_alert(self):
        cfg = _cfg(alert_on_slow=True, slow_threshold_seconds=0.0)
        with patch("pipewatch.monitor.send_slack_alert") as mock_alert:
            run_pipeline("echo slow", cfg)
        mock_alert.assert_called_once()

    def test_timeout_marks_result(self):
        with patch("pipewatch.monitor.send_slack_alert"):
            result = run_pipeline("sleep 5", _cfg(), timeout=0.01)
        assert result.timed_out is True
        assert result.exit_code == -1

    def test_no_alert_without_webhook(self):
        cfg = _cfg(webhook_url="")
        with patch("pipewatch.monitor.send_slack_alert") as mock_alert:
            run_pipeline("exit 2", cfg)
        mock_alert.assert_not_called()
