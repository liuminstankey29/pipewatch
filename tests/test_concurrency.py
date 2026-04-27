"""Tests for pipewatch.concurrency."""
from __future__ import annotations

import pytest

from pipewatch.concurrency import ConcurrencyPolicy


@pytest.fixture()
def policy(tmp_path):
    return ConcurrencyPolicy(max_concurrent=2, state_dir=str(tmp_path), pipeline="pipe1")


def test_disabled_when_zero(tmp_path):
    p = ConcurrencyPolicy(max_concurrent=0, state_dir=str(tmp_path), pipeline="p")
    assert not p.is_enabled()


def test_enabled_when_positive(policy):
    assert policy.is_enabled()


def test_describe_disabled(tmp_path):
    p = ConcurrencyPolicy(max_concurrent=0, state_dir=str(tmp_path), pipeline="p")
    assert "disabled" in p.describe()


def test_describe_enabled(policy):
    desc = policy.describe()
    assert "2" in desc
    assert "disabled" not in desc


def test_acquire_allowed_up_to_max(policy):
    assert policy.acquire() is True
    assert policy.acquire() is True


def test_acquire_blocked_over_max(policy):
    policy.acquire()
    policy.acquire()
    assert policy.acquire() is False


def test_release_frees_slot(policy):
    policy.acquire()
    policy.acquire()
    policy.release()
    assert policy.acquire() is True


def test_active_count_zero_initially(policy):
    assert policy.active_count() == 0


def test_active_count_increments(policy):
    policy.acquire()
    assert policy.active_count() == 1
    policy.acquire()
    assert policy.active_count() == 2


def test_reset_clears_state(policy):
    policy.acquire()
    policy.acquire()
    policy.reset()
    assert policy.active_count() == 0


def test_disabled_always_acquires(tmp_path):
    p = ConcurrencyPolicy(max_concurrent=0, state_dir=str(tmp_path), pipeline="p")
    for _ in range(10):
        assert p.acquire() is True


def test_different_pipelines_independent(tmp_path):
    p1 = ConcurrencyPolicy(max_concurrent=1, state_dir=str(tmp_path), pipeline="a")
    p2 = ConcurrencyPolicy(max_concurrent=1, state_dir=str(tmp_path), pipeline="b")
    assert p1.acquire() is True
    # p1 is now at limit but p2 should be unaffected
    assert p2.acquire() is True
