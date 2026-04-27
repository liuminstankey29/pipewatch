"""Tests for pipewatch.cli_dependency."""
from __future__ import annotations

import argparse

import pytest

from pipewatch.cli_dependency import (
    add_dependency_args,
    policy_from_args,
    policy_from_config,
    resolve_dependency,
)


def _parse(argv: list) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_dependency_args(p)
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# add_dependency_args / defaults
# ---------------------------------------------------------------------------

def test_defaults():
    args = _parse([])
    assert args.require == []
    assert args.dep_lookback == 1
    assert ".pipewatch/history" in args.dep_history_dir


def test_require_flag_single():
    args = _parse(["--require", "ingest"])
    assert args.require == ["ingest"]


def test_require_flag_multiple():
    args = _parse(["--require", "ingest", "--require", "transform"])
    assert set(args.require) == {"ingest", "transform"}


def test_lookback_flag():
    args = _parse(["--dep-lookback", "5"])
    assert args.dep_lookback == 5


def test_history_dir_flag():
    args = _parse(["--dep-history-dir", "/tmp/hist"])
    assert args.dep_history_dir == "/tmp/hist"


# ---------------------------------------------------------------------------
# policy_from_args
# ---------------------------------------------------------------------------

def test_policy_from_args_no_upstreams():
    args = _parse([])
    policy = policy_from_args(args)
    assert not policy.is_enabled()


def test_policy_from_args_with_upstreams():
    args = _parse(["--require", "a", "--require", "b"])
    policy = policy_from_args(args)
    assert policy.is_enabled()
    assert set(policy.upstreams) == {"a", "b"}


# ---------------------------------------------------------------------------
# policy_from_config
# ---------------------------------------------------------------------------

def test_policy_from_config_empty():
    policy = policy_from_config({})
    assert not policy.is_enabled()


def test_policy_from_config_list():
    cfg = {"dependency": {"upstreams": ["x", "y"], "lookback": 2}}
    policy = policy_from_config(cfg)
    assert policy.upstreams == ["x", "y"]
    assert policy.lookback == 2


def test_policy_from_config_csv_string():
    cfg = {"dependency": {"upstreams": "alpha, beta"}}
    policy = policy_from_config(cfg)
    assert "alpha" in policy.upstreams
    assert "beta" in policy.upstreams


# ---------------------------------------------------------------------------
# resolve_dependency
# ---------------------------------------------------------------------------

def test_resolve_prefers_cli_when_set():
    args = _parse(["--require", "cli-pipe"])
    cfg = {"dependency": {"upstreams": ["cfg-pipe"]}}
    policy = resolve_dependency(args, cfg)
    assert "cli-pipe" in policy.upstreams


def test_resolve_falls_back_to_config():
    args = _parse([])
    cfg = {"dependency": {"upstreams": ["cfg-pipe"]}}
    policy = resolve_dependency(args, cfg)
    assert "cfg-pipe" in policy.upstreams


def test_resolve_no_config_returns_empty_policy():
    args = _parse([])
    policy = resolve_dependency(args)
    assert not policy.is_enabled()
