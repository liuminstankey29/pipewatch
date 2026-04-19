"""Tests for pipewatch.quota."""
import time
import pytest
from pipewatch.quota import QuotaPolicy


@pytest.fixture
def policy(tmp_path):
    return QuotaPolicy(max_runs=3, period_seconds=3600, state_dir=str(tmp_path))


def test_disabled_when_zero(tmp_path):
    p = QuotaPolicy(max_runs=0, state_dir=str(tmp_path))
    assert not p.is_enabled()


def test_enabled_when_positive(policy):
    assert policy.is_enabled()


def test_describe_disabled(tmp_path):
    p = QuotaPolicy(max_runs=0, state_dir=str(tmp_path))
    assert "disabled" in p.describe()


def test_describe_enabled(policy):
    desc = policy.describe()
    assert "3" in desc
    assert "1h" in desc


def test_not_exceeded_before_any_record(policy):
    assert not policy.is_exceeded("pipe")


def test_allows_up_to_max(policy):
    now = time.time()
    for i in range(3):
        assert not policy.is_exceeded("pipe", now=now + i)
        policy.record("pipe", now=now + i)


def test_exceeded_after_max(policy):
    now = time.time()
    for i in range(3):
        policy.record("pipe", now=now + i)
    assert policy.is_exceeded("pipe", now=now + 3)


def test_old_records_pruned(policy):
    old = time.time() - 7200  # 2 h ago, outside 1 h window
    for i in range(3):
        policy.record("pipe", now=old + i)
    assert not policy.is_exceeded("pipe")  # all pruned


def test_reset_clears_state(policy):
    now = time.time()
    for i in range(3):
        policy.record("pipe", now=now + i)
    policy.reset("pipe")
    assert not policy.is_exceeded("pipe")


def test_different_pipelines_independent(policy):
    now = time.time()
    for i in range(3):
        policy.record("pipe_a", now=now + i)
    assert policy.is_exceeded("pipe_a", now=now + 3)
    assert not policy.is_exceeded("pipe_b", now=now + 3)
