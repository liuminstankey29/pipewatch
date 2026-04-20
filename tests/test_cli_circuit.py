"""Tests for pipewatch.cli_circuit."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.cli_circuit import (
    add_circuit_args,
    policy_from_args,
    policy_from_config,
    resolve_circuit,
)
from pipewatch.circuit import CircuitBreakerPolicy


def _parse(*argv):
    parser = argparse.ArgumentParser()
    add_circuit_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.circuit_max_failures == 0
    assert args.circuit_reset == 300


def test_max_failures_flag():
    args = _parse("--circuit-max-failures", "5")
    assert args.circuit_max_failures == 5


def test_reset_flag():
    args = _parse("--circuit-reset", "120")
    assert args.circuit_reset == 120


def test_state_dir_flag(tmp_path):
    args = _parse("--circuit-state-dir", str(tmp_path))
    assert args.circuit_state_dir == str(tmp_path)


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args)
    assert not p.is_enabled()


def test_policy_from_args_enabled():
    args = _parse("--circuit-max-failures", "3")
    p = policy_from_args(args)
    assert p.is_enabled()
    assert p.max_failures == 3


def test_policy_from_config_defaults():
    class FakeCfg:
        circuit = {}
    p = policy_from_config(FakeCfg())
    assert not p.is_enabled()


def test_policy_from_config_values():
    class FakeCfg:
        circuit = {"max_failures": 4, "reset_seconds": 90}
    p = policy_from_config(FakeCfg())
    assert p.max_failures == 4
    assert p.reset_seconds == 90


def test_resolve_prefers_cli_when_set():
    class FakeCfg:
        circuit = {"max_failures": 2}
    args = _parse("--circuit-max-failures", "7")
    p = resolve_circuit(args, FakeCfg())
    assert p.max_failures == 7


def test_resolve_falls_back_to_config():
    class FakeCfg:
        circuit = {"max_failures": 2}
    args = _parse()  # CLI disabled
    p = resolve_circuit(args, FakeCfg())
    assert p.max_failures == 2
