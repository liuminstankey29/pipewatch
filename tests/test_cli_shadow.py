"""Tests for pipewatch.cli_shadow."""
from __future__ import annotations

import argparse

import pytest

from pipewatch.cli_shadow import add_shadow_args, policy_from_args, policy_from_config, resolve_shadow
from pipewatch.shadow import ShadowPolicy


def _parse(*argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_shadow_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.shadow is False
    assert args.shadow_label == "shadow"


def test_shadow_flag():
    args = _parse("--shadow")
    assert args.shadow is True


def test_shadow_label_flag():
    args = _parse("--shadow", "--shadow-label", "canary")
    assert args.shadow_label == "canary"


def test_policy_from_args_disabled():
    args = _parse()
    p = policy_from_args(args)
    assert isinstance(p, ShadowPolicy)
    assert not p.is_enabled()


def test_policy_from_args_enabled():
    args = _parse("--shadow", "--shadow-label", "beta")
    p = policy_from_args(args)
    assert p.is_enabled()
    assert p.label == "beta"


def test_policy_from_config_disabled():
    p = policy_from_config({})
    assert not p.is_enabled()


def test_policy_from_config_enabled():
    p = policy_from_config({"shadow": {"enabled": True, "label": "dark"}})
    assert p.is_enabled()
    assert p.label == "dark"


def test_resolve_shadow_prefers_cli_flag():
    args = _parse("--shadow")
    p = resolve_shadow(args, cfg={"shadow": {"enabled": False}})
    assert p.is_enabled()


def test_resolve_shadow_falls_back_to_config():
    args = _parse()
    p = resolve_shadow(args, cfg={"shadow": {"enabled": True, "label": "cfg"}})
    assert p.is_enabled()
    assert p.label == "cfg"


def test_resolve_shadow_defaults_when_no_config():
    args = _parse()
    p = resolve_shadow(args)
    assert not p.is_enabled()
