"""Tests for pipewatch.dependency."""
from __future__ import annotations

import pytest

from pipewatch.dependency import (
    DependencyPolicy,
    DependencyResult,
    check_dependencies,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeHistory:
    """Minimal stand-in for RunHistory."""
    def __init__(self, data: dict):
        self._data = data  # pipeline -> list[bool]

    def last_for(self, name: str, limit: int = 1):
        entries = self._data.get(name)
        if entries is None:
            return []
        return entries[-limit:]


class _FakeBoolEntry:
    def __init__(self, ok: bool):
        self._ok = ok

    def succeeded(self) -> bool:
        return self._ok


def _ok():
    return _FakeBoolEntry(True)


def _fail():
    return _FakeBoolEntry(False)


# ---------------------------------------------------------------------------
# DependencyPolicy
# ---------------------------------------------------------------------------

def test_disabled_when_no_upstreams():
    p = DependencyPolicy()
    assert not p.is_enabled()


def test_enabled_when_upstreams_set():
    p = DependencyPolicy(upstreams=["ingest"])
    assert p.is_enabled()


def test_describe_disabled():
    assert "disabled" in DependencyPolicy().describe()


def test_describe_enabled():
    p = DependencyPolicy(upstreams=["a", "b"], lookback=2)
    desc = p.describe()
    assert "a" in desc and "b" in desc
    assert "2" in desc


# ---------------------------------------------------------------------------
# DependencyResult
# ---------------------------------------------------------------------------

def test_result_passed_message():
    r = DependencyResult(passed=True)
    assert "satisfied" in r.message()


def test_result_failed_message():
    r = DependencyResult(passed=False, failed_upstreams=["etl"])
    assert "etl" in r.message()
    assert "failed" in r.message()


def test_result_missing_message():
    r = DependencyResult(passed=False, missing_upstreams=["load"])
    assert "load" in r.message()
    assert "no history" in r.message()


# ---------------------------------------------------------------------------
# check_dependencies (with monkeypatching)
# ---------------------------------------------------------------------------

def test_no_upstreams_passes(monkeypatch):
    policy = DependencyPolicy()
    result = check_dependencies(policy)
    assert result.passed


def test_all_upstreams_ok(monkeypatch):
    policy = DependencyPolicy(upstreams=["a", "b"])
    fake = _FakeHistory({"a": [_ok()], "b": [_ok()]})
    monkeypatch.setattr("pipewatch.dependency.RunHistory", lambda _dir: fake)
    result = check_dependencies(policy)
    assert result.passed
    assert result.failed_upstreams == []
    assert result.missing_upstreams == []


def test_one_upstream_failed(monkeypatch):
    policy = DependencyPolicy(upstreams=["a", "b"])
    fake = _FakeHistory({"a": [_ok()], "b": [_fail()]})
    monkeypatch.setattr("pipewatch.dependency.RunHistory", lambda _dir: fake)
    result = check_dependencies(policy)
    assert not result.passed
    assert "b" in result.failed_upstreams


def test_missing_upstream(monkeypatch):
    policy = DependencyPolicy(upstreams=["ghost"])
    fake = _FakeHistory({})
    monkeypatch.setattr("pipewatch.dependency.RunHistory", lambda _dir: fake)
    result = check_dependencies(policy)
    assert not result.passed
    assert "ghost" in result.missing_upstreams


def test_history_exception_treated_as_missing(monkeypatch):
    policy = DependencyPolicy(upstreams=["boom"])
    def _bad(_dir):
        raise OSError("disk gone")
    monkeypatch.setattr("pipewatch.dependency.RunHistory", _bad)
    result = check_dependencies(policy)
    assert not result.passed
    assert "boom" in result.missing_upstreams


def test_lookback_checks_multiple_runs(monkeypatch):
    policy = DependencyPolicy(upstreams=["pipe"], lookback=3)
    # last 3 runs: two ok, one fail
    fake = _FakeHistory({"pipe": [_ok(), _fail(), _ok()]})
    monkeypatch.setattr("pipewatch.dependency.RunHistory", lambda _dir: fake)
    result = check_dependencies(policy)
    assert not result.passed
    assert "pipe" in result.failed_upstreams
