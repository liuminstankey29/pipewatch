"""Tests for pipewatch.cli_digest."""
from __future__ import annotations

import argparse

from pipewatch.cli_digest import add_digest_args, period_from_args


def _parse(*args: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_digest_args(parser)
    return parser.parse_args(list(args))


def test_defaults():
    ns = _parse()
    assert ns.pipeline is None
    assert ns.period == 24
    assert ns.send is False


def test_pipeline_flag():
    ns = _parse("--pipeline", "etl")
    assert ns.pipeline == "etl"


def test_period_flag():
    ns = _parse("--period", "48")
    assert ns.period == 48


def test_send_flag():
    ns = _parse("--send")
    assert ns.send is True


def test_period_from_args_explicit():
    ns = _parse("--period", "12")
    assert period_from_args(ns) == 12


def test_period_from_args_default():
    ns = _parse()
    assert period_from_args(ns, cfg=None) == 24
