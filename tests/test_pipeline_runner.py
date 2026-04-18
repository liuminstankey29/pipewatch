"""Tests for pipewatch.pipeline_runner."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.hooks import HookConfig
from pipewatch.monitor import RunResult
from pipewatch.pipeline_runner import PipelineRunSummary, run_with_hooks


def _cfg():
    from pipewatch.config import Config
    return Config(webhook_url="https://hooks.slack.com/x", pipeline_name="test")


def _ok_result():
    return RunResult(returncode=0, stdout="ok", stderr="", timed_out=False, duration=0.1)


def _fail_result():
    return RunResult(returncode=1, stdout="", stderr="err", timed_out=False, duration=0.1)


@patch("pipewatch.pipeline_runner.run_pipeline")
def test_pre_and_post_hooks_called(mock_run):
    mock_run.return_value = _ok_result()
    hc = HookConfig(
        pre=[f"{sys.executable} -c 'pass'"],
        post=[f"{sys.executable} -c 'pass'"],
    )
    summary = run_with_hooks("echo hi", _cfg(), hook_cfg=hc)
    assert summary.succeeded
    assert len(summary.pre_results) == 1
    assert len(summary.post_results) == 1
    assert summary.pre_results[0].succeeded


@patch("pipewatch.pipeline_runner.run_pipeline")
def test_failure_hooks_called_on_failure(mock_run):
    mock_run.return_value = _fail_result()
    hc = HookConfig(on_failure=[f"{sys.executable} -c 'pass'"])
    summary = run_with_hooks("echo hi", _cfg(), hook_cfg=hc)
    assert not summary.succeeded
    assert len(summary.failure_results) == 1


@patch("pipewatch.pipeline_runner.run_pipeline")
def test_failure_hooks_not_called_on_success(mock_run):
    mock_run.return_value = _ok_result()
    hc = HookConfig(on_failure=[f"{sys.executable} -c 'raise SystemExit(1)'"])
    summary = run_with_hooks("echo hi", _cfg(), hook_cfg=hc)
    assert summary.succeeded
    assert summary.failure_results == []


@patch("pipewatch.pipeline_runner.run_pipeline")
def test_no_hooks_runs_cleanly(mock_run):
    mock_run.return_value = _ok_result()
    summary = run_with_hooks("echo hi", _cfg())
    assert summary.pre_results == []
    assert summary.post_results == []
    assert summary.failure_results == []


@patch("pipewatch.pipeline_runner.run_pipeline")
def test_summary_succeeded_property(mock_run):
    mock_run.return_value = _ok_result()
    summary = run_with_hooks("echo hi", _cfg())
    assert summary.succeeded is True

    mock_run.return_value = _fail_result()
    summary2 = run_with_hooks("echo hi", _cfg())
    assert summary2.succeeded is False
