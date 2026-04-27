"""Tests for pipewatch.spillover."""
from __future__ import annotations

import pytest

from pipewatch.spillover import (
    SpilloverPolicy,
    SpilloverResult,
    evaluate_spillover,
)


# ---------------------------------------------------------------------------
# SpilloverPolicy
# ---------------------------------------------------------------------------

class TestSpilloverPolicy:
    def test_disabled_by_default(self):
        p = SpilloverPolicy()
        assert not p.is_enabled()

    def test_enabled_with_warn(self):
        p = SpilloverPolicy(warn_seconds=60.0)
        assert p.is_enabled()

    def test_enabled_with_max(self):
        p = SpilloverPolicy(max_seconds=120.0)
        assert p.is_enabled()

    def test_describe_disabled(self):
        assert SpilloverPolicy().describe() == "spillover: disabled"

    def test_describe_warn_only(self):
        p = SpilloverPolicy(warn_seconds=30.0)
        assert "warn>30.0s" in p.describe()

    def test_describe_max_only(self):
        p = SpilloverPolicy(max_seconds=90.0)
        assert "max>90.0s" in p.describe()

    def test_describe_both(self):
        p = SpilloverPolicy(warn_seconds=30.0, max_seconds=90.0)
        desc = p.describe()
        assert "warn>30.0s" in desc
        assert "max>90.0s" in desc


# ---------------------------------------------------------------------------
# SpilloverResult
# ---------------------------------------------------------------------------

class TestSpilloverResult:
    def test_no_breach_no_warn(self):
        r = SpilloverResult(elapsed=10.0, warn_seconds=60.0, max_seconds=120.0)
        assert not r.warned
        assert not r.breached

    def test_warn_triggered(self):
        r = SpilloverResult(elapsed=65.0, warn_seconds=60.0, max_seconds=120.0)
        assert r.warned
        assert not r.breached

    def test_breach_triggered(self):
        r = SpilloverResult(elapsed=130.0, warn_seconds=60.0, max_seconds=120.0)
        assert r.warned
        assert r.breached

    def test_message_ok(self):
        r = SpilloverResult(elapsed=5.0, warn_seconds=60.0, max_seconds=None)
        assert "within" in r.message()

    def test_message_warn(self):
        r = SpilloverResult(elapsed=70.0, warn_seconds=60.0, max_seconds=None)
        assert "approaching" in r.message()

    def test_message_breach(self):
        r = SpilloverResult(elapsed=130.0, warn_seconds=60.0, max_seconds=120.0)
        assert "exceeded" in r.message()


# ---------------------------------------------------------------------------
# evaluate_spillover
# ---------------------------------------------------------------------------

def test_evaluate_returns_none_when_disabled():
    assert evaluate_spillover(SpilloverPolicy(), 999.0) is None


def test_evaluate_returns_result_when_enabled():
    p = SpilloverPolicy(warn_seconds=30.0)
    r = evaluate_spillover(p, 50.0)
    assert isinstance(r, SpilloverResult)
    assert r.elapsed == 50.0
    assert r.warned
