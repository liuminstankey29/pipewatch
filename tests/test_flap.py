"""Tests for pipewatch.flap — flap detection logic."""
import pytest
from unittest.mock import MagicMock
from pipewatch.flap import FlapPolicy, FlapResult, analyze_flap


def _entry(ok: bool):
    e = MagicMock()
    e.succeeded.return_value = ok
    return e


# ---------------------------------------------------------------------------
# FlapPolicy
# ---------------------------------------------------------------------------

def test_disabled_by_default():
    p = FlapPolicy()
    assert not p.is_enabled()


def test_enabled_when_min_flaps_set():
    p = FlapPolicy(min_flaps=3, window=6)
    assert p.is_enabled()


def test_disabled_when_window_too_small():
    p = FlapPolicy(min_flaps=2, window=1)
    assert not p.is_enabled()


def test_describe_disabled():
    assert "disabled" in FlapPolicy().describe()


def test_describe_enabled():
    desc = FlapPolicy(min_flaps=3, window=8).describe()
    assert "3" in desc
    assert "8" in desc


# ---------------------------------------------------------------------------
# FlapResult
# ---------------------------------------------------------------------------

def test_is_flapping_true():
    r = FlapResult(flap_count=4, threshold=3, window=10)
    assert r.is_flapping


def test_is_flapping_false():
    r = FlapResult(flap_count=2, threshold=3, window=10)
    assert not r.is_flapping


def test_message_stable():
    r = FlapResult(flap_count=1, threshold=3, window=10, transitions=["ok", "fail"])
    assert "stable" in r.message()


def test_message_flapping_contains_transitions():
    r = FlapResult(flap_count=4, threshold=3, window=6,
                   transitions=["ok", "fail", "ok", "fail", "ok", "fail"])
    msg = r.message()
    assert "flapping" in msg
    assert "→" in msg


# ---------------------------------------------------------------------------
# analyze_flap
# ---------------------------------------------------------------------------

def test_returns_none_when_disabled():
    entries = [_entry(True), _entry(False)]
    assert analyze_flap(FlapPolicy(), entries) is None


def test_no_flap_on_all_success():
    entries = [_entry(True)] * 6
    result = analyze_flap(FlapPolicy(min_flaps=2, window=6), entries)
    assert result is not None
    assert result.flap_count == 0
    assert not result.is_flapping


def test_detects_alternating_flap():
    entries = [_entry(i % 2 == 0) for i in range(6)]  # ok/fail/ok/fail/ok/fail
    result = analyze_flap(FlapPolicy(min_flaps=3, window=6), entries)
    assert result is not None
    assert result.flap_count == 5
    assert result.is_flapping


def test_window_limits_entries():
    # 10 entries but window=4; only last 4 matter — all success → 0 flaps
    entries = [_entry(i % 2 == 0) for i in range(6)] + [_entry(True)] * 4
    result = analyze_flap(FlapPolicy(min_flaps=2, window=4), entries)
    assert result is not None
    assert result.flap_count == 0


def test_too_few_entries_returns_zero_flaps():
    result = analyze_flap(FlapPolicy(min_flaps=2, window=10), [_entry(True)])
    assert result is not None
    assert result.flap_count == 0
