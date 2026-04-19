"""Tests for pipewatch.cli_baseline."""
from __future__ import annotations
import argparse
from unittest.mock import MagicMock
from pipewatch.cli_baseline import (
    add_baseline_args,
    policy_from_args,
    policy_from_config,
    resolve_baseline,
)


def _parse(*argv):
    p = argparse.ArgumentParser()
    add_baseline_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.baseline is False
    assert args.baseline_window == 20
    assert args.baseline_threshold == 2.0


def test_baseline_flag():
    args = _parse("--baseline")
    assert args.baseline is True


def test_window_flag():
    args = _parse("--baseline-window", "5")
    assert args.baseline_window == 5


def test_threshold_flag():
    args = _parse("--baseline-threshold", "3.5")
    assert args.baseline_threshold == 3.5


def test_policy_from_args_enabled():
    args = _parse("--baseline", "--baseline-window", "10", "--baseline-threshold", "1.5")
    p = policy_from_args(args)
    assert p.enabled
    assert p.window == 10
    assert p.threshold == 1.5


def test_policy_from_config_defaults():
    cfg = MagicMock()
    cfg.baseline = {}
    p = policy_from_config(cfg)
    assert not p.enabled
    assert p.window == 20
    assert p.threshold == 2.0


def test_policy_from_config_values():
    cfg = MagicMock()
    cfg.baseline = {"enabled": True, "window": 15, "threshold": 3.0}
    p = policy_from_config(cfg)
    assert p.enabled
    assert p.window == 15
    assert p.threshold == 3.0


def test_resolve_baseline_args_override():
    cfg = MagicMock()
    cfg.baseline = {"enabled": False, "window": 20, "threshold": 2.0}
    args = _parse("--baseline", "--baseline-window", "7")
    p = resolve_baseline(args, cfg)
    assert p.enabled
    assert p.window == 7
