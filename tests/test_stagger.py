"""Tests for pipewatch.stagger."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewatch.stagger import StaggerPolicy, stagger_from_config


def _policy(window: int = 60, pipeline: str = "myjob", seed: str = "") -> StaggerPolicy:
    mock_sleep = MagicMock()
    return StaggerPolicy(
        window_seconds=window,
        pipeline=pipeline,
        seed=seed,
        _sleep=mock_sleep,
    )


class TestStaggerPolicy:
    def test_disabled_when_zero(self):
        p = _policy(window=0)
        assert not p.is_enabled()

    def test_enabled_when_positive(self):
        p = _policy(window=30)
        assert p.is_enabled()

    def test_describe_disabled(self):
        p = _policy(window=0)
        assert "disabled" in p.describe()

    def test_describe_enabled_contains_window(self):
        p = _policy(window=120)
        desc = p.describe()
        assert "120s" in desc
        assert "stagger" in desc

    def test_apply_returns_none_when_disabled(self):
        p = _policy(window=0)
        result = p.apply()
        assert result is None
        p._sleep.assert_not_called()

    def test_apply_sleeps_and_returns_offset(self):
        p = _policy(window=60, pipeline="alpha")
        result = p.apply()
        assert result is not None
        assert 0.0 <= result < 60.0
        p._sleep.assert_called_once_with(result)

    def test_offset_is_deterministic(self):
        p1 = _policy(window=100, pipeline="pipe-a", seed="x")
        p2 = _policy(window=100, pipeline="pipe-a", seed="x")
        assert p1._offset() == p2._offset()

    def test_offset_differs_by_pipeline(self):
        p1 = _policy(window=100, pipeline="pipe-a")
        p2 = _policy(window=100, pipeline="pipe-b")
        assert p1._offset() != p2._offset()

    def test_offset_within_window(self):
        for name in ["alpha", "beta", "gamma", "delta"]:
            p = _policy(window=300, pipeline=name)
            offset = p._offset()
            assert 0.0 <= offset < 300.0

    def test_seed_changes_offset(self):
        p1 = _policy(window=100, pipeline="job", seed="run-1")
        p2 = _policy(window=100, pipeline="job", seed="run-2")
        assert p1._offset() != p2._offset()


def test_stagger_from_config_disabled():
    cfg = MagicMock(stagger_window=0, pipeline="p", stagger_seed="")
    policy = stagger_from_config(cfg)
    assert not policy.is_enabled()


def test_stagger_from_config_enabled():
    cfg = MagicMock(stagger_window=45, pipeline="etl", stagger_seed="abc")
    policy = stagger_from_config(cfg)
    assert policy.is_enabled()
    assert policy.window_seconds == 45
    assert policy.pipeline == "etl"
    assert policy.seed == "abc"


def test_stagger_from_config_missing_attrs():
    cfg = MagicMock(spec=[])
    policy = stagger_from_config(cfg)
    assert not policy.is_enabled()
