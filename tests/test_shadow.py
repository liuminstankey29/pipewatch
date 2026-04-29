"""Tests for pipewatch.shadow."""
from __future__ import annotations

import sys
from unittest.mock import patch, MagicMock

import pytest

from pipewatch.shadow import ShadowPolicy, ShadowResult, run_shadow


# ---------------------------------------------------------------------------
# ShadowPolicy
# ---------------------------------------------------------------------------

class TestShadowPolicy:
    def test_disabled_by_default(self):
        p = ShadowPolicy()
        assert not p.is_enabled()

    def test_enabled_when_flag_set(self):
        p = ShadowPolicy(enabled=True)
        assert p.is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in ShadowPolicy().describe()

    def test_describe_enabled(self):
        p = ShadowPolicy(enabled=True, label="canary")
        desc = p.describe()
        assert "enabled" in desc
        assert "canary" in desc


# ---------------------------------------------------------------------------
# ShadowResult
# ---------------------------------------------------------------------------

def _policy(enabled=True, label="shadow"):
    return ShadowPolicy(enabled=enabled, label=label)


def test_succeeded_zero_exit():
    r = ShadowResult(policy=_policy(), exit_code=0)
    assert r.succeeded()


def test_failed_nonzero_exit():
    r = ShadowResult(policy=_policy(), exit_code=1)
    assert not r.succeeded()


def test_summary_ok():
    r = ShadowResult(policy=_policy(label="canary"), exit_code=0, elapsed=1.23)
    s = r.summary()
    assert "canary" in s
    assert "ok" in s
    assert "1.2" in s


def test_summary_failure():
    r = ShadowResult(policy=_policy(), exit_code=2)
    assert "exit=2" in r.summary()


# ---------------------------------------------------------------------------
# run_shadow
# ---------------------------------------------------------------------------

def test_run_shadow_disabled_returns_none():
    result = run_shadow(ShadowPolicy(enabled=False), command="echo hi")
    assert result is None


def test_run_shadow_success():
    p = ShadowPolicy(enabled=True)
    result = run_shadow(p, command="echo hello")
    assert result is not None
    assert result.succeeded()
    assert result.elapsed is not None and result.elapsed >= 0


def test_run_shadow_failure():
    p = ShadowPolicy(enabled=True)
    result = run_shadow(p, command=f"{sys.executable} -c 'import sys; sys.exit(3)'")
    assert result is not None
    assert not result.succeeded()
    assert result.exit_code == 3


def test_run_shadow_timeout():
    p = ShadowPolicy(enabled=True)
    result = run_shadow(p, command=f"{sys.executable} -c 'import time; time.sleep(10)'" , timeout=0.05)
    assert result is not None
    assert result.exit_code == -1
    assert "timed out" in result.notes
