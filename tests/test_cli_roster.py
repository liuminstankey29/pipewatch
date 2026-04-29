"""Tests for pipewatch.cli_roster."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.cli_roster import add_roster_args, handle_roster_cmd
from pipewatch.roster import load_roster


@pytest.fixture()
def rdir(tmp_path):
    return str(tmp_path)


def _parse(*argv):
    p = argparse.ArgumentParser()
    add_roster_args(p)
    return p.parse_args(list(argv))


def test_register_creates_entry(rdir):
    args = _parse("register", "etl", "--owner", "alice", "--tag", "prod")
    rc = handle_roster_cmd(args, rdir)
    assert rc == 0
    r = load_roster(rdir)
    e = r.get("etl")
    assert e is not None
    assert e.owner == "alice"
    assert "prod" in e.tags
    assert e.enabled is True


def test_register_disabled(rdir):
    args = _parse("register", "etl", "--disabled")
    handle_roster_cmd(args, rdir)
    r = load_roster(rdir)
    assert r.get("etl").enabled is False


def test_list_empty(rdir, capsys):
    args = _parse("list")
    rc = handle_roster_cmd(args, rdir)
    assert rc == 0
    out = capsys.readouterr().out
    assert "no pipelines" in out


def test_list_shows_registered(rdir, capsys):
    reg_args = _parse("register", "etl", "--owner", "bob")
    handle_roster_cmd(reg_args, rdir)
    list_args = _parse("list")
    handle_roster_cmd(list_args, rdir)
    out = capsys.readouterr().out
    assert "etl" in out
    assert "bob" in out


def test_remove_existing(rdir):
    handle_roster_cmd(_parse("register", "etl"), rdir)
    rc = handle_roster_cmd(_parse("remove", "etl"), rdir)
    assert rc == 0
    assert load_roster(rdir).get("etl") is None


def test_remove_missing_returns_1(rdir):
    rc = handle_roster_cmd(_parse("remove", "nope"), rdir)
    assert rc == 1


def test_toggle_disables(rdir):
    handle_roster_cmd(_parse("register", "etl"), rdir)
    rc = handle_roster_cmd(_parse("toggle", "etl", "--disable"), rdir)
    assert rc == 0
    assert load_roster(rdir).get("etl").enabled is False


def test_toggle_enables(rdir):
    handle_roster_cmd(_parse("register", "etl", "--disabled"), rdir)
    rc = handle_roster_cmd(_parse("toggle", "etl", "--enable"), rdir)
    assert rc == 0
    assert load_roster(rdir).get("etl").enabled is True


def test_toggle_flips_when_no_flag(rdir):
    handle_roster_cmd(_parse("register", "etl"), rdir)
    handle_roster_cmd(_parse("toggle", "etl"), rdir)
    assert load_roster(rdir).get("etl").enabled is False


def test_toggle_missing_returns_1(rdir):
    rc = handle_roster_cmd(_parse("toggle", "nope"), rdir)
    assert rc == 1


def test_no_subcommand_returns_1(rdir):
    p = argparse.ArgumentParser()
    add_roster_args(p)
    args = p.parse_args([])
    rc = handle_roster_cmd(args, rdir)
    assert rc == 1
