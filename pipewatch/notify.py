"""Notification routing: decides when and how to send alerts based on history and config."""

from __future__ import annotations

from typing import Optional

from pipewatch.config import Config
from pipewatch.history import HistoryEntry, RunHistory
from pipewatch.monitor import RunResult
from pipewatch.slack import send_slack_alert, format_pipeline_message


def _should_alert(result: RunResult, last: Optional[HistoryEntry], cfg: Config) -> bool:
    """Return True if a Slack alert should be sent for this result."""
    if not cfg.webhook_url:
        return False

    # Always alert on failure
    if not result.succeeded:
        return True

    # Alert on recovery: previous run failed, this one succeeded
    if last is not None and not last.succeeded:
        return True

    return False


def _alert_type(result: RunResult, last: Optional[HistoryEntry]) -> str:
    if result.succeeded:
        return "recovery"
    if result.timed_out:
        return "timeout"
    return "failure"


def notify(
    pipeline_name: str,
    result: RunResult,
    history: RunHistory,
    cfg: Config,
) -> bool:
    """Record result in history and send alert if needed. Returns True if alert was sent."""
    last = history.last_for(pipeline_name)

    entry = HistoryEntry(
        pipeline=pipeline_name,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        duration=result.duration,
    )
    history.record(entry)

    if not _should_alert(result, last, cfg):
        return False

    alert_type = _alert_type(result, last)
    text = format_pipeline_message(
        pipeline_name=pipeline_name,
        alert_type=alert_type,
        exit_code=result.exit_code,
        duration=result.duration,
    )
    send_slack_alert(cfg.webhook_url, text)
    return True
