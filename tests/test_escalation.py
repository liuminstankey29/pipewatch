"""Tests for pipewatch.escalation."""
from __future__ import annotations

import time
import pytest
from pathlib import Path
from pipewatch.escalation import EscalationPolicy


@pytest.fixture
def policy(tmp_path):
    return EscalationPolicy(
        enabled=True,
        after_seconds=60,
        max_pings=3,
        state_dir=str(tmp_path),
    )


def test_disabled_when_zero():
    p = EscalationPolicy(enabled=False, after_seconds=0)
    assert not p.is_enabled()


def test_enabled_when_positive():
    p = EscalationPolicy(enabled=True, after_seconds=30)
    assert p.is_enabled()


def test_describe_disabled():
    p = EscalationPolicy()
    assert "disabled" in p.describe()


def test_describe_enabled():
    p = EscalationPolicy(enabled=True, after_seconds=120, max_pings=2)
    desc = p.describe()
    assert "120s" in desc
    assert "2 pings" in desc


def test_not_escalating_before_record(policy):
    assert not policy.should_escalate("pipe1")


def test_not_escalating_immediately_after_record(policy):
    policy.record_failure("pipe1")
    # just recorded — not yet past after_seconds
    assert not policy.should_escalate("pipe1")


def test_escalates_after_threshold(policy, tmp_path):
    policy.after_seconds = 0  # always past threshold
    policy.record_failure("pipe2")
    assert policy.should_escalate("pipe2")


def test_record_ping_increments(policy):
    policy.after_seconds = 0
    policy.record_failure("pipe3")
    policy.record_ping("pipe3")
    state = policy._load("pipe3")
    assert state["ping_count"] == 1


def test_max_pings_blocks_escalation(policy):
    policy.after_seconds = 0
    policy.max_pings = 1
    policy.record_failure("pipe4")
    assert policy.should_escalate("pipe4")
    policy.record_ping("pipe4")
    assert not policy.should_escalate("pipe4")


def test_clear_removes_state(policy):
    policy.record_failure("pipe5")
    policy.clear("pipe5")
    assert not policy._state_path("pipe5").exists()


def test_clear_missing_is_noop(policy):
    policy.clear("nonexistent")  # should not raise


def test_record_failure_idempotent_timestamp(policy):
    policy.record_failure("pipe6")
    t1 = policy._load("pipe6")["first_failed_at"]
    time.sleep(0.05)
    policy.record_failure("pipe6")  # second call should not overwrite
    t2 = policy._load("pipe6")["first_failed_at"]
    assert t1 == t2
