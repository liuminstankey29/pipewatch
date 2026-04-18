"""Tests for pipewatch.retry."""
import pytest
from unittest.mock import patch, MagicMock

from pipewatch.monitor import RunResult
from pipewatch.retry import RetryPolicy, RetryResult, run_with_retry


def _ok() -> RunResult:
    return RunResult(exit_code=0, stdout="", stderr="", elapsed=1.0, timed_out=False)


def _fail() -> RunResult:
    return RunResult(exit_code=1, stdout="", stderr="err", elapsed=1.0, timed_out=False)


def _timeout() -> RunResult:
    return RunResult(exit_code=None, stdout="", stderr="", elapsed=5.0, timed_out=True)


def _no_sleep(s):
    pass


def test_succeeds_first_attempt():
    policy = RetryPolicy(max_attempts=3)
    r = run_with_retry(lambda: _ok(), policy, sleep_fn=_no_sleep)
    assert r.succeeded
    assert r.attempts == 1


def test_retries_until_success():
    calls = [_fail(), _fail(), _ok()]
    it = iter(calls)
    policy = RetryPolicy(max_attempts=3, delay_seconds=1.0)
    r = run_with_retry(lambda: next(it), policy, sleep_fn=_no_sleep)
    assert r.succeeded
    assert r.attempts == 3
    assert len(r.history) == 3


def test_exhausts_all_attempts():
    policy = RetryPolicy(max_attempts=3, delay_seconds=0.0)
    r = run_with_retry(lambda: _fail(), policy, sleep_fn=_no_sleep)
    assert not r.succeeded
    assert r.attempts == 3


def test_no_retry_on_timeout_by_default():
    policy = RetryPolicy(max_attempts=3)
    r = run_with_retry(lambda: _timeout(), policy, sleep_fn=_no_sleep)
    assert r.attempts == 1
    assert r.final.timed_out


def test_retry_on_timeout_when_enabled():
    calls = [_timeout(), _ok()]
    it = iter(calls)
    policy = RetryPolicy(max_attempts=3, retry_on_timeout=True, delay_seconds=0.0)
    r = run_with_retry(lambda: next(it), policy, sleep_fn=_no_sleep)
    assert r.succeeded
    assert r.attempts == 2


def test_sleep_called_between_attempts():
    sleeps = []
    calls = [_fail(), _ok()]
    it = iter(calls)
    policy = RetryPolicy(max_attempts=3, delay_seconds=4.0, backoff_factor=2.0)
    run_with_retry(lambda: next(it), policy, sleep_fn=sleeps.append)
    assert len(sleeps) == 1
    assert sleeps[0] == pytest.approx(4.0)


def test_backoff_delays():
    policy = RetryPolicy(max_attempts=4, delay_seconds=2.0, backoff_factor=3.0)
    delays = list(policy.delays())
    assert delays == pytest.approx([2.0, 6.0, 18.0])
