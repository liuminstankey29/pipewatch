"""Tests for pipewatch.sampling and pipewatch.cli_sampling."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.sampling import SamplingPolicy
from pipewatch.cli_sampling import add_sampling_args, policy_from_args, policy_from_config, resolve_sampling


# ---------------------------------------------------------------------------
# SamplingPolicy unit tests
# ---------------------------------------------------------------------------

class TestSamplingPolicy:
    def test_disabled_by_default(self):
        p = SamplingPolicy()
        assert not p.is_enabled()

    def test_enabled_below_one(self):
        p = SamplingPolicy(rate=0.5)
        assert p.is_enabled()

    def test_rate_zero_is_enabled(self):
        p = SamplingPolicy(rate=0.0)
        assert p.is_enabled()

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            SamplingPolicy(rate=1.5)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            SamplingPolicy(rate=-0.1)

    def test_describe_disabled(self):
        assert "disabled" in SamplingPolicy(rate=1.0).describe()

    def test_describe_enabled(self):
        desc = SamplingPolicy(rate=0.25).describe()
        assert "25%" in desc

    def test_always_runs_when_rate_one(self):
        p = SamplingPolicy(rate=1.0)
        assert all(p.should_run() for _ in range(20))

    def test_never_runs_when_rate_zero(self):
        p = SamplingPolicy(rate=0.0)
        assert not any(p.should_run() for _ in range(20))

    def test_deterministic_with_seed(self):
        p1 = SamplingPolicy(rate=0.5, seed=42)
        p2 = SamplingPolicy(rate=0.5, seed=42)
        results1 = [p1.should_run() for _ in range(50)]
        results2 = [p2.should_run() for _ in range(50)]
        assert results1 == results2

    def test_approximate_rate(self):
        p = SamplingPolicy(rate=0.5, seed=0)
        runs = sum(p.should_run() for _ in range(1000))
        # Allow ±10% tolerance
        assert 400 <= runs <= 600


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*argv):
    parser = argparse.ArgumentParser()
    add_sampling_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.sample_rate is None


def test_sample_rate_flag():
    args = _parse("--sample-rate", "0.3")
    assert args.sample_rate == pytest.approx(0.3)


def test_policy_from_args_uses_flag():
    args = _parse("--sample-rate", "0.7")
    p = policy_from_args(args)
    assert p.rate == pytest.approx(0.7)


def test_policy_from_args_default_is_one():
    args = _parse()
    args.sample_rate = None
    p = policy_from_args(args)
    assert p.rate == pytest.approx(1.0)
    assert not p.is_enabled()


def test_policy_from_config():
    class Cfg:
        sample_rate = "0.2"
    p = policy_from_config(Cfg())
    assert p.rate == pytest.approx(0.2)


def test_resolve_prefers_cli():
    class Cfg:
        sample_rate = "0.9"
    args = _parse("--sample-rate", "0.1")
    p = resolve_sampling(args, Cfg())
    assert p.rate == pytest.approx(0.1)


def test_resolve_falls_back_to_config():
    class Cfg:
        sample_rate = "0.6"
    args = _parse()
    p = resolve_sampling(args, Cfg())
    assert p.rate == pytest.approx(0.6)
