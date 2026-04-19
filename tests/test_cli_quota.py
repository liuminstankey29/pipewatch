"""Tests for pipewatch.cli_quota."""
import argparse
import pytest
from pipewatch.cli_quota import add_quota_args, policy_from_args, policy_from_config


def _parse(*argv):
    p = argparse.ArgumentParser()
    add_quota_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.quota_max == 0
    assert args.quota_period == 86400
    assert args.quota_state_dir == "/tmp/pipewatch/quota"


def test_quota_max_flag():
    args = _parse("--quota-max", "10")
    assert args.quota_max == 10


def test_quota_period_flag():
    args = _parse("--quota-period", "3600")
    assert args.quota_period == 3600


def test_quota_state_dir_flag():
    args = _parse("--quota-state-dir", "/var/quota")
    assert args.quota_state_dir == "/var/quota"


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args)
    assert not p.is_enabled()


def test_policy_from_args_enabled():
    args = _parse("--quota-max", "5", "--quota-period", "7200")
    p = policy_from_args(args)
    assert p.is_enabled()
    assert p.max_runs == 5
    assert p.period_seconds == 7200


def test_policy_from_config_empty():
    class Cfg:
        quota = {}
    p = policy_from_config(Cfg())
    assert not p.is_enabled()


def test_policy_from_config_values():
    class Cfg:
        quota = {"max_runs": 20, "period_seconds": 1800}
    p = policy_from_config(Cfg())
    assert p.max_runs == 20
    assert p.period_seconds == 1800
