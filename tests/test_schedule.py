"""Tests for pipewatch.schedule."""
import pytest
from datetime import datetime

from pipewatch.schedule import Schedule, _matches, from_config


def _dt(minute=0, hour=12, day=1, month=6, weekday=2):
    # weekday: Monday=0 … Sunday=6
    # datetime(2024, 6, 5) is a Wednesday (weekday=2)
    return datetime(2024, month, day, hour, minute)


class TestMatches:
    def test_wildcard(self):
        assert _matches("*", 99)

    def test_exact(self):
        assert _matches("30", 30)
        assert not _matches("30", 31)

    def test_step(self):
        assert _matches("*/15", 0)
        assert _matches("*/15", 30)
        assert not _matches("*/15", 7)

    def test_range(self):
        assert _matches("9-17", 12)
        assert not _matches("9-17", 8)

    def test_list(self):
        assert _matches("1,15,30", 15)
        assert not _matches("1,15,30", 16)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            _matches("abc", 1)


class TestSchedule:
    def test_is_due_wildcard(self):
        s = Schedule("* * * * *")
        assert s.is_due(_dt())

    def test_exact_match(self):
        s = Schedule("0 12 1 6 *")
        assert s.is_due(_dt(minute=0, hour=12, day=1, month=6))

    def test_not_due(self):
        s = Schedule("0 9 * * *")
        assert not s.is_due(_dt(hour=12, minute=0))

    def test_wrong_field_count(self):
        with pytest.raises(ValueError):
            Schedule("* * *")

    def test_next_description(self):
        s = Schedule("0 6 * * *")
        assert "0 6 * * *" in s.next_description()

    def test_from_config(self):
        s = from_config("*/5 * * * *")
        assert isinstance(s, Schedule)
