"""Tests for pipewatch.schedule_runner."""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from pipewatch.config import Config
from pipewatch.history import RunHistory
from pipewatch.monitor import RunResult
from pipewatch.retry import RetryPolicy, RetryResult
from pipewatch.schedule import Schedule
from pipewatch.schedule_runner import ScheduleRunner


def _cfg():
    return Config(name="etl", command="echo hi", webhook="https://hooks.slack.com/x")


def _always_due():
    s = MagicMock(spec=Schedule)
    s.is_due.return_value = True
    s.next_description.return_value = "cron(* * * * *)"
    return s


def _never_due():
    s = MagicMock(spec=Schedule)
    s.is_due.return_value = False
    s.next_description.return_value = "cron(0 0 31 2 *)"
    return s


def _mock_result(ok=True):
    run = MagicMock(spec=RunResult)
    run.succeeded.return_value = ok
    rr = MagicMock(spec=RetryResult)
    rr.final = run
    rr.attempts = 1
    return rr


@pytest.fixture()
def history(tmp_path):
    return RunHistory(path=tmp_path / "hist.json")


class TestScheduleRunner:
    def test_no_execution_when_not_due(self, history):
        runner = ScheduleRunner(
            config=_cfg(), schedule=_never_due(), history=history, _tick_seconds=0
        )
        with patch("pipewatch.schedule_runner.run_with_retry") as rwr:
            runner.run_loop(max_ticks=3)
            rwr.assert_not_called()

    def test_executes_when_due(self, history):
        runner = ScheduleRunner(
            config=_cfg(), schedule=_always_due(), history=history, _tick_seconds=0
        )
        mock_res = _mock_result(ok=True)
        with patch("pipewatch.schedule_runner.run_with_retry", return_value=mock_res), \
             patch("pipewatch.schedule_runner.notify") as mock_notify:
            runner.run_loop(max_ticks=1)
            mock_notify.assert_called_once()

    def test_records_history_after_run(self, history):
        runner = ScheduleRunner(
            config=_cfg(), schedule=_always_due(), history=history, _tick_seconds=0
        )
        mock_res = _mock_result(ok=False)
        with patch("pipewatch.schedule_runner.run_with_retry", return_value=mock_res), \
             patch("pipewatch.schedule_runner.notify"):
            runner.run_loop(max_ticks=1)
        assert history.last_for("etl") is not None
