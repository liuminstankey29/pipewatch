"""Tests for pipewatch.cli_escalation and cli_escalation_integration."""
from __future__ import annotations

import argparse
import pytest
from unittest.mock import patch, MagicMock

from pipewatch.cli_escalation import (
    add_escalation_args,
    policy_from_args,
    policy_from_config,
    resolve_escalation,
)
from pipewatch.cli_escalation_integration import handle_run_result, check_and_escalate
from pipewatch.escalation import EscalationPolicy


def _parse(*argv):
    p = argparse.ArgumentParser()
    add_escalation_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.escalate_after == 0
    assert args.escalate_max_pings == 0


def test_escalate_after_flag():
    args = _parse("--escalate-after", "300")
    assert args.escalate_after == 300


def test_max_pings_flag():
    args = _parse("--escalate-max-pings", "5")
    assert args.escalate_max_pings == 5


def test_policy_from_args_disabled():
    args = _parse()
    pol = policy_from_args(args)
    assert not pol.is_enabled()


def test_policy_from_args_enabled():
    args = _parse("--escalate-after", "120")
    pol = policy_from_args(args)
    assert pol.is_enabled()
    assert pol.after_seconds == 120


def test_policy_from_config_disabled():
    cfg = MagicMock()
    cfg.escalation = {}
    pol = policy_from_config(cfg)
    assert not pol.is_enabled()


def test_policy_from_config_enabled():
    cfg = MagicMock()
    cfg.escalation = {"after_seconds": 60, "max_pings": 2}
    pol = policy_from_config(cfg)
    assert pol.is_enabled()
    assert pol.after_seconds == 60
    assert pol.max_pings == 2


def test_resolve_prefers_cli(tmp_path):
    args = _parse("--escalate-after", "90", "--escalate-state-dir", str(tmp_path))
    cfg = MagicMock()
    cfg.escalation = {"after_seconds": 999}
    pol = resolve_escalation(args, cfg)
    assert pol.after_seconds == 90


def test_handle_run_result_success_clears(tmp_path):
    pol = EscalationPolicy(enabled=True, after_seconds=0, state_dir=str(tmp_path))
    pol.record_failure("p")
    outcome = handle_run_result(pol, "p", succeeded=True)
    assert not pol._state_path("p").exists()
    assert not outcome.escalated


def test_handle_run_result_failure_escalates(tmp_path):
    pol = EscalationPolicy(enabled=True, after_seconds=0, state_dir=str(tmp_path))
    with patch("pipewatch.cli_escalation_integration.send_slack_alert") as mock_send:
        outcome = handle_run_result(pol, "p", succeeded=False, webhook_url="https://hooks.example.com")
    assert outcome.escalated
    mock_send.assert_called_once()


def test_check_and_escalate_disabled(tmp_path):
    pol = EscalationPolicy(enabled=False, after_seconds=0, state_dir=str(tmp_path))
    outcome = check_and_escalate(pol, "p", webhook_url=None)
    assert not outcome.checked
    assert not outcome.escalated
