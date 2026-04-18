"""Simple text report generator from run history."""

from __future__ import annotations

from typing import List

from pipewatch.history import HistoryEntry, RunHistory


def _status_icon(entry: HistoryEntry) -> str:
    return "✓" if entry.succeeded else "✗"


def format_entry(entry: HistoryEntry) -> str:
    icon = _status_icon(entry)
    extra = " (timed out)" if entry.timed_out else ""
    return (
        f"  [{icon}] {entry.timestamp}  pipeline={entry.pipeline}"
        f"  exit={entry.exit_code}{extra}"
        f"  duration={entry.duration_seconds:.1f}s"
    )


def summary_report(history: RunHistory, pipeline: str | None = None, n: int = 10) -> str:
    entries: List[HistoryEntry] = (
        history.last_for(pipeline, n) if pipeline else history.last(n)
    )
    if not entries:
        return "No history found."

    total = len(entries)
    passed = sum(1 for e in entries if e.succeeded)
    failed = total - passed
    avg_dur = sum(e.duration_seconds for e in entries) / total

    lines = [
        f"Pipeline history{'  filter=' + pipeline if pipeline else ''}  (last {total} runs)",
        f"  Passed: {passed}  Failed: {failed}  Avg duration: {avg_dur:.1f}s",
        "-" * 60,
    ]
    lines.extend(format_entry(e) for e in reversed(entries))
    return "\n".join(lines)


def print_report(history: RunHistory, pipeline: str | None = None, n: int = 10) -> None:
    print(summary_report(history, pipeline=pipeline, n=n))
