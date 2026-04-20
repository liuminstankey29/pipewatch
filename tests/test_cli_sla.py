"""Tests for pipewatch.cli_sla."""
import argparse
import pytest

from pipewatch.cli_sla import add_sla_args, policy_from_args, policy_from_config, resolve_sla
from pipewatch.sla import SLAPolicy


def _parse(*argv):
    parser = argparse.ArgumentParser()
    add_sla_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.sla_warn is None
    assert args.sla_max is None


def test_warn_flag():
    args = _parse("--sla-warn", "45")
    assert args.sla_warn == 45.0


def test_max_flag():
    args = _parse("--sla-max", "120")
    assert args.sla_max == 120.0


def test_both_flags():
    args = _parse("--sla-warn", "30", "--sla-max", "90")
    assert args.sla_warn == 30.0
    assert args.sla_max == 90.0


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args)
    assert not p.is_enabled()


def test_policy_from_args_enabled():
    args = _parse("--sla-max", "60")
    p = policy_from_args(args, pipeline="etl")
    assert p.is_enabled()
    assert p.max_seconds == 60.0
    assert p.pipeline == "etl"


def test_policy_from_config():
    cfg = {"sla": {"warn_seconds": 20, "max_seconds": 80}}
    p = policy_from_config(cfg, pipeline="load")
    assert p.warn_seconds == 20
    assert p.max_seconds == 80
    assert p.pipeline == "load"


def test_policy_from_config_missing_key():
    p = policy_from_config({}, pipeline="x")
    assert not p.is_enabled()


def test_resolve_sla_prefers_args():
    args = _parse("--sla-max", "50")
    cfg = {"sla": {"max_seconds": 999}}
    p = resolve_sla(args, cfg=cfg, pipeline="p")
    assert p.max_seconds == 50.0


def test_resolve_sla_falls_back_to_config():
    args = _parse()
    cfg = {"sla": {"max_seconds": 200}}
    p = resolve_sla(args, cfg=cfg, pipeline="p")
    assert p.max_seconds == 200


def test_resolve_sla_returns_empty_when_no_source():
    args = _parse()
    p = resolve_sla(args, cfg=None, pipeline="p")
    assert not p.is_enabled()
