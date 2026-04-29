"""Focused CLI-layer tests for cli_replay (resolve logic and edge cases)."""
from __future__ import annotations

import argparse

import pytest

from pipewatch.cli_replay import (
    add_replay_args,
    policy_from_args,
    policy_from_config,
    resolve_replay,
)


def _parse(*args):
    p = argparse.ArgumentParser()
    add_replay_args(p)
    return p.parse_args(list(args))


def test_replay_dir_default():
    ns = _parse()
    policy = policy_from_args(ns)
    assert policy.snapshot_dir == ".pipewatch/snapshots"


def test_replay_dir_custom():
    ns = _parse("--replay", "s1", "--replay-dir", "/tmp/snaps")
    policy = policy_from_args(ns)
    assert policy.snapshot_dir == "/tmp/snaps"


def test_policy_from_config_custom_dir():
    cfg = {"replay": {"snapshot_id": "x", "snapshot_dir": "/data/snaps"}}
    policy = policy_from_config(cfg)
    assert policy.snapshot_dir == "/data/snaps"


def test_policy_from_config_dry_run_false_by_default():
    cfg = {"replay": {"snapshot_id": "x"}}
    policy = policy_from_config(cfg)
    assert not policy.dry_run


def test_resolve_no_cli_no_config():
    ns = _parse()
    policy = resolve_replay(ns, {})
    assert not policy.is_enabled()


def test_resolve_cli_takes_precedence_over_config():
    ns = _parse("--replay", "from_cli")
    cfg = {"replay": {"snapshot_id": "from_cfg"}}
    policy = resolve_replay(ns, cfg)
    assert policy.snapshot_id == "from_cli"


def test_resolve_config_used_when_cli_absent():
    ns = _parse()
    cfg = {"replay": {"snapshot_id": "from_cfg", "dry_run": False}}
    policy = resolve_replay(ns, cfg)
    assert policy.snapshot_id == "from_cfg"
    assert policy.is_enabled()
