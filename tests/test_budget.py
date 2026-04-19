"""Tests for pipewatch.budget and pipewatch.cli_budget."""
import argparse
import pytest
from pipewatch.budget import BudgetPolicy, BudgetResult, check_budget
from pipewatch.cli_budget import add_budget_args, policy_from_args, policy_from_config


class TestBudgetPolicy:
    def test_disabled_by_default(self):
        assert not BudgetPolicy().is_enabled()

    def test_enabled_with_max(self):
        assert BudgetPolicy(max_seconds=60).is_enabled()

    def test_enabled_with_warn(self):
        assert BudgetPolicy(warn_seconds=30).is_enabled()

    def test_describe_disabled(self):
        assert BudgetPolicy().describe() == "disabled"

    def test_describe_warn_only(self):
        assert "warn>" in BudgetPolicy(warn_seconds=30).describe()

    def test_describe_max(self):
        desc = BudgetPolicy(max_seconds=60, hard_fail=True).describe()
        assert "max=60" in desc and "hard_fail=True" in desc


class TestCheckBudget:
    def test_disabled_policy_always_ok(self):
        r = check_budget(BudgetPolicy(), elapsed=9999)
        assert r.succeeded()
        assert not r.warned and not r.exceeded

    def test_under_warn_threshold(self):
        r = check_budget(BudgetPolicy(warn_seconds=60), elapsed=30)
        assert not r.warned

    def test_over_warn_threshold(self):
        r = check_budget(BudgetPolicy(warn_seconds=60), elapsed=90)
        assert r.warned and not r.exceeded
        assert r.succeeded()
        assert "warning" in r.message

    def test_over_max_soft(self):
        r = check_budget(BudgetPolicy(max_seconds=60, hard_fail=False), elapsed=90)
        assert r.exceeded and not r.hard_fail
        assert r.succeeded()
        assert "exceeded" in r.message

    def test_over_max_hard_fail(self):
        r = check_budget(BudgetPolicy(max_seconds=60, hard_fail=True), elapsed=90)
        assert r.exceeded and r.hard_fail
        assert not r.succeeded()

    def test_exactly_at_max_not_exceeded(self):
        r = check_budget(BudgetPolicy(max_seconds=60), elapsed=60)
        assert not r.exceeded


def _parse(argv):
    p = argparse.ArgumentParser()
    add_budget_args(p)
    return p.parse_args(argv)


def test_defaults():
    args = _parse([])
    policy = policy_from_args(args)
    assert not policy.is_enabled()
    assert not policy.hard_fail


def test_warn_flag():
    policy = policy_from_args(_parse(["--budget-warn", "45"]))
    assert policy.warn_seconds == 45


def test_max_and_hard_fail():
    policy = policy_from_args(_parse(["--budget-max", "120", "--budget-hard-fail"]))
    assert policy.max_seconds == 120
    assert policy.hard_fail


def test_policy_from_config():
    class Cfg:
        budget = {"max_seconds": 300, "warn_seconds": 200, "hard_fail": True}
    p = policy_from_config(Cfg())
    assert p.max_seconds == 300
    assert p.warn_seconds == 200
    assert p.hard_fail


def test_policy_from_config_missing():
    class Cfg:
        budget = None
    p = policy_from_config(Cfg())
    assert not p.is_enabled()
