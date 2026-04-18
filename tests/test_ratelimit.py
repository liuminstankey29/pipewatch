"""Tests for pipewatch.ratelimit."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.ratelimit import (
    RateLimitPolicy,
    check_and_record,
    reset,
)


@pytest.fixture()
def policy(tmp_path: Path) -> RateLimitPolicy:
    return RateLimitPolicy(max_alerts=3, window_seconds=60, state_file=tmp_path / "rl.json")


def test_disabled_when_zero_max(tmp_path):
    p = RateLimitPolicy(max_alerts=0, state_file=tmp_path / "rl.json")
    assert not p.is_enabled()
    # should always allow
    assert check_and_record(p) is True
    assert check_and_record(p) is True


def test_allows_up_to_max(policy):
    for _ in range(3):
        assert check_and_record(policy) is True


def test_blocks_over_max(policy):
    for _ in range(3):
        check_and_record(policy)
    assert check_and_record(policy) is False


def test_reset_clears_state(policy):
    for _ in range(3):
        check_and_record(policy)
    reset(policy)
    assert check_and_record(policy) is True


def test_per_pipeline_isolation(tmp_path):
    p = RateLimitPolicy(max_alerts=1, window_seconds=60, state_file=tmp_path / "rl.json")
    assert check_and_record(p, pipeline="etl") is True
    assert check_and_record(p, pipeline="etl") is False
    # different pipeline should still be allowed
    assert check_and_record(p, pipeline="ingest") is True


def test_window_expiry(tmp_path, monkeypatch):
    p = RateLimitPolicy(max_alerts=2, window_seconds=10, state_file=tmp_path / "rl.json")
    fake_now = [time.time() - 20]  # start 20 s in the past

    original_time = time.time

    def _fake_time():
        return fake_now[0]

    monkeypatch.setattr("pipewatch.ratelimit.time.time", _fake_time)
    check_and_record(p)
    check_and_record(p)
    # both timestamps are outside the 10-s window when we move forward
    fake_now[0] = original_time()
    assert check_and_record(p) is True
