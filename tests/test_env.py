"""Tests for pipewatch.env and pipewatch.cli_env."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.env import PipelineEnv, parse_env_pairs, env_from_config
from pipewatch.cli_env import add_env_args, env_from_args, resolve_env


# ---------------------------------------------------------------------------
# parse_env_pairs
# ---------------------------------------------------------------------------

def test_parse_env_pairs_basic():
    result = parse_env_pairs(["FOO=bar", "BAZ=qux"])
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_pairs_value_contains_equals():
    result = parse_env_pairs(["URL=http://x.com?a=1"])
    assert result["URL"] == "http://x.com?a=1"


def test_parse_env_pairs_invalid_raises():
    with pytest.raises(ValueError, match="KEY=VALUE"):
        parse_env_pairs(["NOEQUALS"])


# ---------------------------------------------------------------------------
# PipelineEnv
# ---------------------------------------------------------------------------

def test_build_merges_onto_base():
    env = PipelineEnv(extras={"MY_VAR": "hello"})
    result = env.build(base={"EXISTING": "yes"})
    assert result["EXISTING"] == "yes"
    assert result["MY_VAR"] == "hello"


def test_build_extras_override_base():
    env = PipelineEnv(extras={"K": "new"})
    result = env.build(base={"K": "old"})
    assert result["K"] == "new"


def test_safe_repr_masks_secret_keys():
    env = PipelineEnv(extras={"API_KEY": "s3cr3t", "NAME": "alice"})
    safe = env.safe_repr()
    assert safe["API_KEY"] == "***"
    assert safe["NAME"] == "alice"


def test_safe_repr_masks_explicit_secret_keys():
    env = PipelineEnv(extras={"TOKEN": "abc", "MY_PASS": "xyz"}, secret_keys=["MY_PASS"])
    safe = env.safe_repr()
    assert safe["TOKEN"] == "***"
    assert safe["MY_PASS"] == "***"


# ---------------------------------------------------------------------------
# env_from_config
# ---------------------------------------------------------------------------

def test_env_from_config_none_returns_empty():
    env = env_from_config(None)
    assert env.extras == {}


def test_env_from_config_detects_secrets():
    env = env_from_config({"SLACK_TOKEN": "t", "STAGE": "prod"})
    assert "SLACK_TOKEN" in env.secret_keys
    assert "STAGE" not in env.secret_keys


# ---------------------------------------------------------------------------
# cli_env helpers
# ---------------------------------------------------------------------------

def _parse(*argv: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_env_args(p)
    return p.parse_args(list(argv))


def test_env_from_args_empty():
    args = _parse()
    env = env_from_args(args)
    assert env.extras == {}


def test_env_from_args_single():
    args = _parse("--env", "FOO=bar")
    env = env_from_args(args)
    assert env.extras == {"FOO": "bar"}


def test_resolve_env_cli_overrides_config():
    args = _parse("--env", "STAGE=staging")
    env = resolve_env(args, cfg=None)
    assert env.extras["STAGE"] == "staging"
