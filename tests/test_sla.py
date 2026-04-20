"""Tests for pipewatch.sla."""
import pytest
from pipewatch.sla import SLAPolicy, SLAResult, check_sla


# ---------------------------------------------------------------------------
# SLAPolicy
# ---------------------------------------------------------------------------

class TestSLAPolicy:
    def test_disabled_by_default(self):
        p = SLAPolicy()
        assert not p.is_enabled()

    def test_enabled_with_warn(self):
        p = SLAPolicy(warn_seconds=60)
        assert p.is_enabled()

    def test_enabled_with_max(self):
        p = SLAPolicy(max_seconds=120)
        assert p.is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in SLAPolicy().describe()

    def test_describe_warn_only(self):
        desc = SLAPolicy(warn_seconds=30).describe()
        assert "warn" in desc
        assert "30" in desc

    def test_describe_max_only(self):
        desc = SLAPolicy(max_seconds=90).describe()
        assert "breach" in desc
        assert "90" in desc

    def test_describe_both(self):
        desc = SLAPolicy(warn_seconds=30, max_seconds=90).describe()
        assert "warn" in desc
        assert "breach" in desc


# ---------------------------------------------------------------------------
# SLAResult
# ---------------------------------------------------------------------------

def _policy(warn=None, max_s=None):
    return SLAPolicy(warn_seconds=warn, max_seconds=max_s)


def test_ok_within_both_thresholds():
    r = SLAResult(elapsed=10.0, policy=_policy(warn=30, max_s=60))
    assert not r.breached
    assert not r.warned
    assert "OK" in r.message()


def test_warn_between_thresholds():
    r = SLAResult(elapsed=45.0, policy=_policy(warn=30, max_s=60))
    assert not r.breached
    assert r.warned
    assert "warning" in r.message().lower()


def test_breach_exceeds_max():
    r = SLAResult(elapsed=75.0, policy=_policy(warn=30, max_s=60))
    assert r.breached
    assert not r.warned
    assert "breached" in r.message().lower()


def test_breach_without_warn_threshold():
    r = SLAResult(elapsed=200.0, policy=_policy(max_s=100))
    assert r.breached


def test_warn_without_max_threshold():
    r = SLAResult(elapsed=50.0, policy=_policy(warn=30))
    assert r.warned
    assert not r.breached


def test_no_thresholds_never_warns_or_breaches():
    r = SLAResult(elapsed=9999.0, policy=_policy())
    assert not r.warned
    assert not r.breached


# ---------------------------------------------------------------------------
# check_sla helper
# ---------------------------------------------------------------------------

def test_check_sla_returns_result():
    p = SLAPolicy(warn_seconds=10, max_seconds=20)
    result = check_sla(elapsed=5.0, policy=p)
    assert isinstance(result, SLAResult)
    assert not result.breached


def test_check_sla_breach(caplog):
    import logging
    p = SLAPolicy(max_seconds=5)
    with caplog.at_level(logging.WARNING, logger="pipewatch.sla"):
        result = check_sla(elapsed=10.0, policy=p)
    assert result.breached
    assert any("SLA breached" in m for m in caplog.messages)
