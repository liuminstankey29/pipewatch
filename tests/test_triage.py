"""Tests for pipewatch.triage."""
import pytest

from pipewatch.triage import (
    CATEGORY_DEPENDENCY,
    CATEGORY_INFRA,
    CATEGORY_OOM,
    CATEGORY_TIMEOUT,
    CATEGORY_UNKNOWN,
    CATEGORY_USER_ERROR,
    TriageResult,
    triage_failure,
)


# ---------------------------------------------------------------------------
# TriageResult helpers
# ---------------------------------------------------------------------------

def test_is_known_true():
    r = TriageResult(category=CATEGORY_OOM, confidence=0.9)
    assert r.is_known is True


def test_is_known_false_for_unknown():
    r = TriageResult(category=CATEGORY_UNKNOWN, confidence=1.0)
    assert r.is_known is False


def test_summary_contains_category():
    r = TriageResult(category=CATEGORY_TIMEOUT, confidence=1.0)
    assert "timeout" in r.summary()
    assert "100%" in r.summary()


# ---------------------------------------------------------------------------
# triage_failure – timeout
# ---------------------------------------------------------------------------

def test_timed_out_returns_timeout_category():
    r = triage_failure(exit_code=-1, timed_out=True)
    assert r.category == CATEGORY_TIMEOUT
    assert r.confidence == 1.0


def test_timed_out_takes_priority_over_stderr():
    r = triage_failure(exit_code=-1, timed_out=True, stderr="out of memory")
    assert r.category == CATEGORY_TIMEOUT


# ---------------------------------------------------------------------------
# triage_failure – OOM
# ---------------------------------------------------------------------------

def test_oom_detected_in_stderr():
    r = triage_failure(exit_code=137, timed_out=False, stderr="Killed: out of memory")
    assert r.category == CATEGORY_OOM
    assert r.confidence >= 0.8


def test_oom_detected_in_stdout():
    r = triage_failure(exit_code=1, timed_out=False, stdout="memory limit exceeded")
    assert r.category == CATEGORY_OOM


# ---------------------------------------------------------------------------
# triage_failure – dependency
# ---------------------------------------------------------------------------

def test_dependency_connection_refused():
    r = triage_failure(exit_code=1, timed_out=False, stderr="connection refused")
    assert r.category == CATEGORY_DEPENDENCY


def test_dependency_no_such_host():
    r = triage_failure(exit_code=1, timed_out=False, stderr="no such host: db.internal")
    assert r.category == CATEGORY_DEPENDENCY


# ---------------------------------------------------------------------------
# triage_failure – infra
# ---------------------------------------------------------------------------

def test_infra_disk_full():
    r = triage_failure(exit_code=1, timed_out=False, stderr="No space left on device")
    assert r.category == CATEGORY_INFRA


# ---------------------------------------------------------------------------
# triage_failure – user error
# ---------------------------------------------------------------------------

def test_user_error_permission_denied():
    r = triage_failure(exit_code=1, timed_out=False, stderr="permission denied: /etc/secret")
    assert r.category == CATEGORY_USER_ERROR


# ---------------------------------------------------------------------------
# triage_failure – unknown
# ---------------------------------------------------------------------------

def test_unknown_when_no_signals():
    r = triage_failure(exit_code=2, timed_out=False, stderr="", stdout="")
    assert r.category == CATEGORY_UNKNOWN
    assert r.confidence == 1.0
    assert "exit_code=2" in (r.note or "")


def test_signals_list_populated():
    r = triage_failure(exit_code=1, timed_out=False, stderr="connection refused")
    assert len(r.signals) > 0
    assert any("connection refused" in s for s in r.signals)
