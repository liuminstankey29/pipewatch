"""Tests for pipewatch.suppression."""
from datetime import datetime

import pytest

from pipewatch.suppression import SuppressionPolicy, _parse_time, suppression_from_config


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    t = _parse_time("08:30")
    assert t.hour == 8 and t.minute == 30


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError, match="Invalid time format"):
        _parse_time("8:5:0")


# ---------------------------------------------------------------------------
# SuppressionPolicy.is_enabled / describe
# ---------------------------------------------------------------------------

def test_disabled_when_no_start_end():
    p = SuppressionPolicy()
    assert not p.is_enabled()


def test_enabled_when_both_set():
    p = SuppressionPolicy(start="22:00", end="06:00")
    assert p.is_enabled()


def test_describe_disabled():
    assert "disabled" in SuppressionPolicy().describe()


def test_describe_enabled():
    p = SuppressionPolicy(start="22:00", end="06:00")
    assert "22:00" in p.describe() and "06:00" in p.describe()


def test_describe_weekdays_only():
    p = SuppressionPolicy(start="01:00", end="02:00", weekdays_only=True)
    assert "weekdays" in p.describe()


# ---------------------------------------------------------------------------
# is_suppressed — same-day window (no midnight wrap)
# ---------------------------------------------------------------------------

def _dt(h, m, weekday=0):  # weekday 0=Monday
    return datetime(2024, 1, 1 + weekday, h, m)  # 2024-01-01 is Monday


def test_inside_window():
    p = SuppressionPolicy(start="22:00", end="23:00")
    assert p.is_suppressed(_dt(22, 30))


def test_outside_window():
    p = SuppressionPolicy(start="22:00", end="23:00")
    assert not p.is_suppressed(_dt(21, 59))


def test_at_window_start_is_suppressed():
    p = SuppressionPolicy(start="22:00", end="23:00")
    assert p.is_suppressed(_dt(22, 0))


def test_at_window_end_is_not_suppressed():
    p = SuppressionPolicy(start="22:00", end="23:00")
    assert not p.is_suppressed(_dt(23, 0))


# ---------------------------------------------------------------------------
# is_suppressed — midnight-wrapping window
# ---------------------------------------------------------------------------

def test_midnight_wrap_before_midnight():
    p = SuppressionPolicy(start="22:00", end="06:00")
    assert p.is_suppressed(_dt(23, 0))


def test_midnight_wrap_after_midnight():
    p = SuppressionPolicy(start="22:00", end="06:00")
    assert p.is_suppressed(_dt(3, 0))


def test_midnight_wrap_outside():
    p = SuppressionPolicy(start="22:00", end="06:00")
    assert not p.is_suppressed(_dt(12, 0))


# ---------------------------------------------------------------------------
# weekdays_only
# ---------------------------------------------------------------------------

def test_weekday_suppressed():
    p = SuppressionPolicy(start="01:00", end="05:00", weekdays_only=True)
    # Monday = weekday 0 → 2024-01-01
    assert p.is_suppressed(datetime(2024, 1, 1, 2, 0))


def test_weekend_not_suppressed():
    p = SuppressionPolicy(start="01:00", end="05:00", weekdays_only=True)
    # Saturday = 2024-01-06
    assert not p.is_suppressed(datetime(2024, 1, 6, 2, 0))


# ---------------------------------------------------------------------------
# suppression_from_config
# ---------------------------------------------------------------------------

def test_from_config_defaults():
    class Cfg:
        suppression = {}
    p = suppression_from_config(Cfg())
    assert not p.is_enabled()


def test_from_config_values():
    class Cfg:
        suppression = {"start": "23:00", "end": "05:00", "weekdays_only": True}
    p = suppression_from_config(Cfg())
    assert p.start == "23:00"
    assert p.end == "05:00"
    assert p.weekdays_only is True
