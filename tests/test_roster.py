"""Tests for pipewatch.roster."""
from __future__ import annotations

import json
import os
import pytest

from pipewatch.roster import (
    Roster,
    RosterEntry,
    format_roster,
    load_roster,
    save_roster,
)


@pytest.fixture()
def rdir(tmp_path):
    return str(tmp_path)


def _entry(name="etl", **kw) -> RosterEntry:
    return RosterEntry(name=name, **kw)


def test_register_and_get():
    r = Roster()
    e = _entry("etl", owner="alice")
    r.register(e)
    assert r.get("etl") is e


def test_get_missing_returns_none():
    r = Roster()
    assert r.get("nope") is None


def test_all_returns_all_entries():
    r = Roster()
    r.register(_entry("a"))
    r.register(_entry("b"))
    names = {e.name for e in r.all()}
    assert names == {"a", "b"}


def test_enabled_filters_disabled():
    r = Roster()
    r.register(_entry("on", enabled=True))
    r.register(_entry("off", enabled=False))
    assert [e.name for e in r.enabled()] == ["on"]


def test_remove_existing():
    r = Roster()
    r.register(_entry("etl"))
    assert r.remove("etl") is True
    assert r.get("etl") is None


def test_remove_missing_returns_false():
    r = Roster()
    assert r.remove("nope") is False


def test_register_overwrites():
    r = Roster()
    r.register(_entry("etl", owner="alice"))
    r.register(_entry("etl", owner="bob"))
    assert r.get("etl").owner == "bob"


def test_save_and_load(rdir):
    r = Roster()
    r.register(_entry("etl", owner="alice", tags=["prod"]))
    r.register(_entry("reports", enabled=False))
    save_roster(r, rdir)
    r2 = load_roster(rdir)
    assert {e.name for e in r2.all()} == {"etl", "reports"}
    assert r2.get("etl").owner == "alice"
    assert r2.get("etl").tags == ["prod"]
    assert r2.get("reports").enabled is False


def test_load_missing_returns_empty(rdir):
    r = load_roster(rdir)
    assert r.all() == []


def test_from_dict_roundtrip():
    e = _entry("etl", description="loads data", owner="team", tags=["a", "b"])
    e2 = RosterEntry.from_dict(e.to_dict())
    assert e2.name == e.name
    assert e2.description == e.description
    assert e2.tags == e.tags


def test_format_roster_empty():
    r = Roster()
    out = format_roster(r)
    assert "no pipelines" in out


def test_format_roster_shows_entries():
    r = Roster()
    r.register(_entry("etl", owner="alice", tags=["prod"]))
    out = format_roster(r)
    assert "etl" in out
    assert "alice" in out
    assert "prod" in out
