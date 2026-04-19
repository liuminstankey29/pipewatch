"""Tests for pipewatch.cooldown."""
import time
import pytest
from pipewatch.cooldown import CooldownPolicy


@pytest.fixture
def policy(tmp_path):
    return CooldownPolicy(pipeline="etl", seconds=60, state_dir=str(tmp_path))


def test_disabled_when_zero(tmp_path):
    p = CooldownPolicy(pipeline="etl", seconds=0, state_dir=str(tmp_path))
    assert not p.is_enabled()


def test_enabled_when_positive(policy):
    assert policy.is_enabled()


def test_not_suppressed_before_record(policy):
    assert not policy.is_suppressed()


def test_suppressed_after_record(policy):
    policy.record()
    assert policy.is_suppressed()


def test_not_suppressed_after_cooldown(tmp_path):
    p = CooldownPolicy(pipeline="etl", seconds=1, state_dir=str(tmp_path))
    p.record()
    time.sleep(1.1)
    assert not p.is_suppressed()


def test_remaining_zero_before_record(policy):
    assert policy.remaining() == 0.0


def test_remaining_positive_after_record(policy):
    policy.record()
    assert policy.remaining() > 0.0
    assert policy.remaining() <= 60.0


def test_remaining_zero_when_disabled(tmp_path):
    p = CooldownPolicy(pipeline="etl", seconds=0, state_dir=str(tmp_path))
    p.record()
    assert p.remaining() == 0.0


def test_reset_clears_state(policy):
    policy.record()
    assert policy.is_suppressed()
    policy.reset()
    assert not policy.is_suppressed()


def test_reset_missing_is_safe(policy):
    policy.reset()  # should not raise


def test_different_pipelines_independent(tmp_path):
    p1 = CooldownPolicy(pipeline="etl", seconds=60, state_dir=str(tmp_path))
    p2 = CooldownPolicy(pipeline="load", seconds=60, state_dir=str(tmp_path))
    p1.record()
    assert p1.is_suppressed()
    assert not p2.is_suppressed()
