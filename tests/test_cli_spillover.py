"""Tests for pipewatch.cli_spillover."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.cli_spillover import (
    add_spillover_args,
    policy_from_args,
    policy_from_config,
    resolve_spillover,
)
from pipewatch.spillover import SpilloverPolicy


def _parse(*argv: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_spillover_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.spillover_warn is None
    assert args.spillover_max is None


def test_warn_flag():
    args = _parse("--spillover-warn", "45")
    assert args.spillover_warn == 45.0


def test_max_flag():
    args = _parse("--spillover-max", "120")
    assert args.spillover_max == 120.0


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args)
    assert not p.is_enabled()


def test_policy_from_args_warn():
    args = _parse("--spillover-warn", "60")
    p = policy_from_args(args)
    assert p.warn_seconds == 60.0
    assert p.max_seconds is None


def test_policy_from_config_empty():
    p = policy_from_config({})
    assert not p.is_enabled()


def test_policy_from_config_values():
    cfg = {"spillover": {"warn_seconds": 30.0, "max_seconds": 90.0}}
    p = policy_from_config(cfg)
    assert p.warn_seconds == 30.0
    assert p.max_seconds == 90.0


def test_resolve_prefers_cli():
    args = _parse("--spillover-warn", "10")
    cfg = {"spillover": {"warn_seconds": 999.0}}
    p = resolve_spillover(args, cfg)
    assert p.warn_seconds == 10.0


def test_resolve_falls_back_to_config():
    args = _parse()
    cfg = {"spillover": {"max_seconds": 200.0}}
    p = resolve_spillover(args, cfg)
    assert p.max_seconds == 200.0


def test_resolve_returns_disabled_with_no_input():
    args = _parse()
    p = resolve_spillover(args)
    assert not p.is_enabled()
