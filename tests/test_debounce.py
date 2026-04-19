"""Tests for pipewatch.debounce."""
import pytest
from pipewatch.debounce import DebouncePolicy


@pytest.fixture
def policy(tmp_path):
    return DebouncePolicy(min_failures=3, state_dir=str(tmp_path))


def test_disabled_when_zero(tmp_path):
    p = DebouncePolicy(min_failures=0, state_dir=str(tmp_path))
    assert not p.is_enabled()


def test_enabled_when_positive(policy):
    assert policy.is_enabled()


def test_describe_disabled(tmp_path):
    p = DebouncePolicy(min_failures=0, state_dir=str(tmp_path))
    assert "disabled" in p.describe()


def test_describe_enabled(policy):
    assert "3" in policy.describe()


def test_not_suppressed_when_disabled(tmp_path):
    p = DebouncePolicy(min_failures=0, state_dir=str(tmp_path))
    # even after recording failures, disabled policy never suppresses
    p.record_failure("pipe")
    assert not p.is_suppressed("pipe")


def test_suppressed_below_threshold(policy):
    policy.record_failure("pipe")
    assert policy.is_suppressed("pipe")
    policy.record_failure("pipe")
    assert policy.is_suppressed("pipe")


def test_not_suppressed_at_threshold(policy):
    for _ in range(3):
        policy.record_failure("pipe")
    assert not policy.is_suppressed("pipe")


def test_not_suppressed_above_threshold(policy):
    for _ in range(5):
        policy.record_failure("pipe")
    assert not policy.is_suppressed("pipe")


def test_record_success_resets(policy):
    for _ in range(3):
        policy.record_failure("pipe")
    policy.record_success("pipe")
    assert policy.is_suppressed("pipe")


def test_different_pipelines_independent(policy):
    for _ in range(3):
        policy.record_failure("pipe-a")
    assert not policy.is_suppressed("pipe-a")
    assert policy.is_suppressed("pipe-b")


def test_reset_clears_state(policy):
    for _ in range(3):
        policy.record_failure("pipe")
    policy.reset("pipe")
    assert policy.is_suppressed("pipe")
