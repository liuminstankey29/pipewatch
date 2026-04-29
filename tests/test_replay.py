"""Tests for pipewatch.replay and pipewatch.cli_replay."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from pipewatch.replay import ReplayPolicy, ReplayResult, load_replay_env
from pipewatch.cli_replay import (
    add_replay_args,
    policy_from_args,
    policy_from_config,
    resolve_replay,
)


# ---------------------------------------------------------------------------
# ReplayPolicy
# ---------------------------------------------------------------------------

class TestReplayPolicy:
    def test_disabled_by_default(self):
        p = ReplayPolicy()
        assert not p.is_enabled()

    def test_enabled_with_snapshot_id(self):
        p = ReplayPolicy(enabled=True, snapshot_id="abc123")
        assert p.is_enabled()

    def test_not_enabled_without_snapshot_id(self):
        p = ReplayPolicy(enabled=True, snapshot_id=None)
        assert not p.is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in ReplayPolicy().describe()

    def test_describe_enabled(self):
        p = ReplayPolicy(enabled=True, snapshot_id="snap1")
        desc = p.describe()
        assert "snap1" in desc
        assert "dry-run" not in desc

    def test_describe_dry_run(self):
        p = ReplayPolicy(enabled=True, snapshot_id="snap1", dry_run=True)
        assert "dry-run" in p.describe()


# ---------------------------------------------------------------------------
# load_replay_env
# ---------------------------------------------------------------------------

def test_load_missing_snapshot(tmp_path):
    policy = ReplayPolicy(enabled=True, snapshot_id="missing", snapshot_dir=str(tmp_path))
    result = load_replay_env(policy)
    assert not result.found
    assert not result.succeeded()
    assert "not found" in result.message


def test_load_existing_snapshot(tmp_path):
    snap = {"env": {"FOO": "bar", "NUM": "42"}}
    (tmp_path / "mysnap.json").write_text(json.dumps(snap))
    policy = ReplayPolicy(enabled=True, snapshot_id="mysnap", snapshot_dir=str(tmp_path))
    result = load_replay_env(policy)
    assert result.found
    assert result.succeeded()
    assert result.env_vars == {"FOO": "bar", "NUM": "42"}


def test_dry_run_message(tmp_path):
    snap = {"env": {"X": "1"}}
    (tmp_path / "ds.json").write_text(json.dumps(snap))
    policy = ReplayPolicy(enabled=True, snapshot_id="ds", snapshot_dir=str(tmp_path), dry_run=True)
    result = load_replay_env(policy)
    assert result.dry_run
    assert "dry-run" in result.message


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*args):
    p = argparse.ArgumentParser()
    add_replay_args(p)
    return p.parse_args(list(args))


def test_defaults():
    ns = _parse()
    policy = policy_from_args(ns)
    assert not policy.is_enabled()


def test_replay_flag():
    ns = _parse("--replay", "snap42")
    policy = policy_from_args(ns)
    assert policy.is_enabled()
    assert policy.snapshot_id == "snap42"


def test_replay_dry_run_flag():
    ns = _parse("--replay", "snap42", "--replay-dry-run")
    policy = policy_from_args(ns)
    assert policy.dry_run


def test_policy_from_config_empty():
    policy = policy_from_config({})
    assert not policy.is_enabled()


def test_policy_from_config_with_snapshot():
    cfg = {"replay": {"snapshot_id": "cfg_snap", "dry_run": True}}
    policy = policy_from_config(cfg)
    assert policy.is_enabled()
    assert policy.snapshot_id == "cfg_snap"
    assert policy.dry_run


def test_resolve_prefers_cli():
    ns = _parse("--replay", "cli_snap")
    cfg = {"replay": {"snapshot_id": "cfg_snap"}}
    policy = resolve_replay(ns, cfg)
    assert policy.snapshot_id == "cli_snap"


def test_resolve_falls_back_to_config():
    ns = _parse()
    cfg = {"replay": {"snapshot_id": "cfg_snap"}}
    policy = resolve_replay(ns, cfg)
    assert policy.snapshot_id == "cfg_snap"
