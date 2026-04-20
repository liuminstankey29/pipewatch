"""Tests for pipewatch.circuit (CircuitBreakerPolicy)."""
from __future__ import annotations

import time
import pytest

from pipewatch.circuit import CircuitBreakerPolicy


@pytest.fixture
def policy(tmp_path):
    return CircuitBreakerPolicy(
        max_failures=3,
        reset_seconds=60,
        state_dir=str(tmp_path),
    )


def test_disabled_when_zero(tmp_path):
    p = CircuitBreakerPolicy(max_failures=0, state_dir=str(tmp_path))
    assert not p.is_enabled()


def test_enabled_when_positive(policy):
    assert policy.is_enabled()


def test_describe_disabled(tmp_path):
    p = CircuitBreakerPolicy(max_failures=0, state_dir=str(tmp_path))
    assert "disabled" in p.describe()


def test_describe_enabled(policy):
    desc = policy.describe()
    assert "3" in desc
    assert "60" in desc


def test_not_open_initially(policy):
    assert not policy.is_open("pipe-a")


def test_not_open_below_threshold(policy):
    policy.record_failure("pipe-a")
    policy.record_failure("pipe-a")
    assert not policy.is_open("pipe-a")


def test_opens_at_threshold(policy):
    for _ in range(3):
        policy.record_failure("pipe-a")
    assert policy.is_open("pipe-a")


def test_success_resets_circuit(policy):
    for _ in range(3):
        policy.record_failure("pipe-a")
    assert policy.is_open("pipe-a")
    policy.record_success("pipe-a")
    assert not policy.is_open("pipe-a")


def test_reset_clears_state(policy):
    for _ in range(3):
        policy.record_failure("pipe-a")
    policy.reset("pipe-a")
    assert not policy.is_open("pipe-a")


def test_different_pipelines_independent(policy):
    for _ in range(3):
        policy.record_failure("pipe-a")
    assert policy.is_open("pipe-a")
    assert not policy.is_open("pipe-b")


def test_half_open_after_reset_window(tmp_path, monkeypatch):
    p = CircuitBreakerPolicy(
        max_failures=2,
        reset_seconds=30,
        state_dir=str(tmp_path),
    )
    for _ in range(2):
        p.record_failure("pipe-x")
    assert p.is_open("pipe-x")
    # Fast-forward past reset window
    monkeypatch.setattr(time, "time", lambda: time.time() + 31)
    assert not p.is_open("pipe-x")  # half-open: allow through


def test_disabled_policy_never_open(tmp_path):
    p = CircuitBreakerPolicy(max_failures=0, state_dir=str(tmp_path))
    for _ in range(10):
        p.record_failure("pipe-z")
    assert not p.is_open("pipe-z")
