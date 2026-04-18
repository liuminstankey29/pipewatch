"""Tests for pipewatch.throttle."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from pipewatch.throttle import ThrottlePolicy


@pytest.fixture()
def policy(tmp_path: Path) -> ThrottlePolicy:
    return ThrottlePolicy(cooldown_seconds=60, state_path=tmp_path / "throttle.json")


def test_disabled_when_zero(tmp_path: Path) -> None:
    p = ThrottlePolicy(cooldown_seconds=0, state_path=tmp_path / "t.json")
    assert not p.is_enabled()
    assert not p.is_suppressed("pipe")


def test_not_suppressed_before_record(policy: ThrottlePolicy) -> None:
    assert not p.is_suppressed("pipe") if (p := policy) else True
    assert not policy.is_suppressed("mypipe")


def test_suppressed_after_record(policy: ThrottlePolicy) -> None:
    policy.record("mypipe")
    assert policy.is_suppressed("mypipe")


def test_different_pipelines_independent(policy: ThrottlePolicy) -> None:
    policy.record("pipe-a")
    assert policy.is_suppressed("pipe-a")
    assert not policy.is_suppressed("pipe-b")


def test_not_suppressed_after_cooldown(tmp_path: Path) -> None:
    p = ThrottlePolicy(cooldown_seconds=1, state_path=tmp_path / "t.json")
    p.record("pipe")
    assert p.is_suppressed("pipe")
    time.sleep(1.05)
    assert not p.is_suppressed("pipe")


def test_reset_single(policy: ThrottlePolicy) -> None:
    policy.record("a")
    policy.record("b")
    policy.reset("a")
    assert not policy.is_suppressed("a")
    assert policy.is_suppressed("b")


def test_reset_all(policy: ThrottlePolicy) -> None:
    policy.record("a")
    policy.record("b")
    policy.reset()
    assert not policy.is_suppressed("a")
    assert not policy.is_suppressed("b")


def test_corrupt_state_file_treated_as_empty(policy: ThrottlePolicy) -> None:
    policy.state_path.write_text("NOT JSON")
    assert not policy.is_suppressed("pipe")
