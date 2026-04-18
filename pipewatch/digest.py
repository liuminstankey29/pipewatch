"""Daily/periodic digest report sent to Slack."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from pipewatch.history import HistoryEntry, RunHistory
from pipewatch.slack import send_slack_alert


@dataclass
class DigestSummary:
    pipeline: Optional[str]
    period_hours: int
    total: int
    successes: int
    failures: int
    avg_duration: Optional[float]  # seconds

    @property
    def failure_rate(self) -> float:
        return self.failures / self.total if self.total else 0.0


def build_digest(history: RunHistory, pipeline: Optional[str] = None, period_hours: int = 24) -> DigestSummary:
    since = datetime.utcnow() - timedelta(hours=period_hours)
    entries: List[HistoryEntry] = [
        e for e in history.all()
        if (pipeline is None or e.pipeline == pipeline)
        and datetime.fromisoformat(e.started_at) >= since
    ]
    successes = sum(1 for e in entries if e.succeeded())
    durations = [e.duration for e in entries if e.duration is not None]
    avg = sum(durations) / len(durations) if durations else None
    return DigestSummary(
        pipeline=pipeline,
        period_hours=period_hours,
        total=len(entries),
        successes=successes,
        failures=len(entries) - successes,
        avg_duration=avg,
    )


def format_digest_message(summary: DigestSummary) -> str:
    label = summary.pipeline or "all pipelines"
    icon = ":white_check_mark:" if summary.failure_rate == 0 else ":warning:"
    avg = f"{summary.avg_duration:.1f}s" if summary.avg_duration is not None else "n/a"
    return (
        f"{icon} *Digest ({summary.period_hours}h) — {label}*\n"
        f"  Runs: {summary.total}  |  "
        f"OK: {summary.successes}  |  "
        f"Failed: {summary.failures}  |  "
        f"Avg duration: {avg}"
    )


def send_digest(webhook_url: str, summary: DigestSummary) -> bool:
    text = format_digest_message(summary)
    return send_slack_alert(webhook_url, text)
