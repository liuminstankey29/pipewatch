"""Tests for pipewatch.jitter."""
import pytest
from unittest.mock import patch

from pipewatch.jitter import JitterPolicy, policy_from_config


class TestJitterPolicy:
    def test_disabled_when_zero(self):
        p = JitterPolicy(max_seconds=0)
        assert not p.is_enabled()

    def test_enabled_when_positive(self):
        p = JitterPolicy(max_seconds=5)
        assert p.is_enabled()

    def test_describe_disabled(self):
        p = JitterPolicy()
        assert "disabled" in p.describe()

    def test_describe_enabled(self):
        p = JitterPolicy(max_seconds=3)
        assert "3" in p.describe()

    def test_delay_zero_when_disabled(self):
        p = JitterPolicy(max_seconds=0)
        assert p.delay() == 0.0

    def test_delay_within_range(self):
        p = JitterPolicy(max_seconds=10, seed=42)
        for _ in range(20):
            d = p.delay()
            assert 0 <= d <= 10

    def test_seed_produces_deterministic_output(self):
        p1 = JitterPolicy(max_seconds=5, seed=7)
        p2 = JitterPolicy(max_seconds=5, seed=7)
        assert p1.delay() == p2.delay()

    def test_sleep_disabled_returns_zero(self):
        p = JitterPolicy(max_seconds=0)
        with patch("pipewatch.jitter.time.sleep") as mock_sleep:
            result = p.sleep()
        mock_sleep.assert_not_called()
        assert result == 0.0

    def test_sleep_enabled_calls_sleep(self):
        p = JitterPolicy(max_seconds=2, seed=1)
        with patch("pipewatch.jitter.time.sleep") as mock_sleep:
            result = p.sleep()
        mock_sleep.assert_called_once_with(result)
        assert 0 <= result <= 2


class TestPolicyFromConfig:
    def test_defaults_when_missing(self):
        p = policy_from_config({})
        assert not p.is_enabled()

    def test_scalar_value(self):
        p = policy_from_config({"jitter": 4.5})
        assert p.max_seconds == 4.5

    def test_dict_value(self):
        p = policy_from_config({"jitter": {"max_seconds": 3, "seed": 99}})
        assert p.max_seconds == 3.0
        assert p.seed == 99

    def test_dict_missing_max_seconds(self):
        p = policy_from_config({"jitter": {}})
        assert p.max_seconds == 0.0
        assert not p.is_enabled()
