"""Tests for pipewatch.cli_throttle."""
from __future__ import annotations

import argparse
from pathlib import Path

from pipewatch.cli_throttle import add_throttle_args, policy_from_args, policy_from_config


def _parse(*args: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_throttle_args(p)
    return p.parse_args(list(args))


def test_defaults() -> None:
    ns = _parse()
    assert ns.throttle == 0
    assert ns.throttle_state is None


def test_throttle_flag() -> None:
    ns = _parse("--throttle", "300")
    assert ns.throttle == 300


def test_state_flag(tmp_path: Path) -> None:
    f = str(tmp_path / "state.json")
    ns = _parse("--throttle-state", f)
    assert ns.throttle_state == f


def test_policy_from_args_disabled() -> None:
    ns = _parse()
    pol = policy_from_args(ns)
    assert not pol.is_enabled()


def test_policy_from_args_enabled() -> None:
    ns = _parse("--throttle", "120")
    pol = policy_from_args(ns)
    assert pol.is_enabled()
    assert pol.cooldown_seconds == 120


def test_policy_from_config_defaults() -> None:
    pol = policy_from_config({})
    assert not pol.is_enabled()


def test_policy_from_config_with_values(tmp_path: Path) -> None:
    cfg = {"throttle_seconds": "90", "throttle_state_path": str(tmp_path / "s.json")}
    pol = policy_from_config(cfg)
    assert pol.cooldown_seconds == 90
    assert pol.state_path == tmp_path / "s.json"
