"""Tests for pipewatch.watchdog and pipewatch.cli_watchdog."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.history import HistoryEntry, RunHistory
from pipewatch.watchdog import WatchdogPolicy, WatchdogResult, check_watchdog
from pipewatch.cli_watchdog import policy_from_args, policy_from_config, resolve_watchdog

import argparse


def _entry(pipeline: str, exit_code: int, minutes_ago: int) -> HistoryEntry:
    ts = datetime.utcnow() - timedelta(minutes=minutes_ago)
    return HistoryEntry(
        pipeline=pipeline,
        timestamp=ts,
        exit_code=exit_code,
        duration=1.0,
        timed_out=False,
        tags={},
    )


@pytest.fixture
def history(tmp_path):
    return RunHistory(path=tmp_path / "h.json")


def test_disabled_policy_never_stale(history):
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=0)
    result = check_watchdog(policy, history)
    assert not result.stale


def test_no_history_is_stale(history):
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=30)
    result = check_watchdog(policy, history)
    assert result.stale
    assert result.last_success is None


def test_recent_success_not_stale(history):
    history.record(_entry("p", 0, minutes_ago=5))
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=30)
    result = check_watchdog(policy, history)
    assert not result.stale


def test_old_success_is_stale(history):
    history.record(_entry("p", 0, minutes_ago=60))
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=30)
    result = check_watchdog(policy, history)
    assert result.stale


def test_failure_does_not_reset_watchdog(history):
    history.record(_entry("p", 1, minutes_ago=5))  # recent but failed
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=30)
    result = check_watchdog(policy, history)
    assert result.stale


def test_message_not_stale(history):
    history.record(_entry("p", 0, minutes_ago=5))
    policy = WatchdogPolicy(pipeline="p", max_silence_minutes=30)
    result = check_watchdog(policy, history)
    assert "last success" in result.message()


def test_message_stale_no_record():
    result = WatchdogResult(pipeline="p", stale=True, last_success=None, max_silence_minutes=30)
    assert "no successful run" in result.message()


def test_policy_from_args():
    ns = argparse.Namespace(watchdog=45)
    p = policy_from_args(ns, "mypipe")
    assert p.max_silence_minutes == 45
    assert p.pipeline == "mypipe"


def test_policy_from_config_missing_attr():
    class Cfg:
        pass
    p = policy_from_config(Cfg(), "mypipe")
    assert not p.is_enabled()


def test_resolve_watchdog_prefers_args():
    ns = argparse.Namespace(watchdog=10)
    class Cfg:
        watchdog_minutes = 999
    p = resolve_watchdog(ns, Cfg(), "p")
    assert p.max_silence_minutes == 10
