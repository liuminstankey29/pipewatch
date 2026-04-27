"""Tests for pipewatch.cli_concurrency."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.cli_concurrency import (
    add_concurrency_args,
    policy_from_args,
    policy_from_config,
    resolve_concurrency,
    _DEFAULT_STATE_DIR,
)
from pipewatch.concurrency import ConcurrencyPolicy


def _parse(*argv):
    parser = argparse.ArgumentParser()
    add_concurrency_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.max_concurrent == 0
    assert args.concurrency_state_dir == _DEFAULT_STATE_DIR


def test_max_concurrent_flag():
    args = _parse("--max-concurrent", "3")
    assert args.max_concurrent == 3


def test_state_dir_flag():
    args = _parse("--concurrency-state-dir", "/tmp/foo")
    assert args.concurrency_state_dir == "/tmp/foo"


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args, pipeline="mypipe")
    assert not p.is_enabled()
    assert p.pipeline == "mypipe"


def test_policy_from_args_enabled():
    args = _parse("--max-concurrent", "2")
    p = policy_from_args(args, pipeline="mypipe")
    assert p.is_enabled()
    assert p.max_concurrent == 2


def test_policy_from_config():
    cfg = {"max_concurrent": "4", "concurrency_state_dir": "/tmp/bar"}
    p = policy_from_config(cfg, pipeline="x")
    assert p.max_concurrent == 4
    assert p.state_dir == "/tmp/bar"
    assert p.pipeline == "x"


def test_resolve_concurrency_prefers_args():
    args = _parse("--max-concurrent", "5")
    cfg = {"max_concurrent": "1"}
    p = resolve_concurrency(args, cfg, pipeline="z")
    assert p.max_concurrent == 5


def test_resolve_concurrency_falls_back_to_config():
    args = _parse()
    cfg = {"max_concurrent": "3"}
    p = resolve_concurrency(args, cfg, pipeline="z")
    assert p.max_concurrent == 3


def test_resolve_concurrency_defaults_when_no_config():
    args = _parse()
    p = resolve_concurrency(args, None, pipeline="z")
    assert not p.is_enabled()
