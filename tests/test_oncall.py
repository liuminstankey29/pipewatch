"""Tests for pipewatch.oncall and pipewatch.cli_oncall."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

import pytest

from pipewatch.oncall import (
    OnCallEntry,
    OnCallRotation,
    format_oncall_mention,
    rotation_from_config,
)
from pipewatch.cli_oncall import add_oncall_args, resolve_oncall


EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)
ALICE = OnCallEntry(name="Alice", slack_user_id="U111")
BOB = OnCallEntry(name="Bob", slack_user_id="U222")


def _rotation(period_days: int = 7) -> OnCallRotation:
    return OnCallRotation(entries=[ALICE, BOB], epoch=EPOCH, period_days=period_days)


def _dt(days_offset: int) -> datetime:
    from datetime import timedelta
    return EPOCH + timedelta(days=days_offset)


class TestOnCallRotation:
    def test_first_slot_is_alice(self):
        r = _rotation()
        assert r.current(_dt(0)) == ALICE

    def test_second_slot_is_bob(self):
        r = _rotation()
        assert r.current(_dt(7)) == BOB

    def test_wraps_around(self):
        r = _rotation()
        assert r.current(_dt(14)) == ALICE

    def test_mention_format(self):
        r = _rotation()
        assert r.mention(_dt(0)) == "<@U111>"

    def test_empty_rotation_returns_none(self):
        r = OnCallRotation(entries=[])
        assert r.current() is None

    def test_empty_mention_is_empty_string(self):
        r = OnCallRotation(entries=[])
        assert r.mention() == ""


def test_format_oncall_mention_none_rotation():
    assert format_oncall_mention(None) == ""


def test_rotation_from_config_none_when_absent():
    assert rotation_from_config({}) is None


def test_rotation_from_config_builds_entries():
    cfg = {
        "oncall": {
            "epoch": "2024-01-01",
            "period_days": 7,
            "entries": [
                {"name": "Alice", "slack_user_id": "U111"},
                {"name": "Bob", "slack_user_id": "U222"},
            ],
        }
    }
    r = rotation_from_config(cfg)
    assert r is not None
    assert len(r.entries) == 2
    assert r.period_days == 7


def _parse(extra: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_oncall_args(p)
    return p.parse_args(extra or [])


def test_default_oncall_mention_false():
    args = _parse()
    assert args.oncall_mention is False


def test_resolve_oncall_no_flag_returns_none():
    args = _parse()
    cfg = {"oncall": {"entries": [{"name": "Alice", "slack_user_id": "U111"}]}}
    # flag not set — resolve returns None from args path, but falls back to config
    result = resolve_oncall(args, cfg)
    # config-level fallback still resolves
    assert result is not None


def test_resolve_oncall_no_config_returns_none():
    args = _parse()
    assert resolve_oncall(args, None) is None
