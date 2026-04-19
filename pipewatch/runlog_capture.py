"""Capture a RunResult + metadata into a RunLog and persist it."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pipewatch.runlog import RunLog, save_log, DEFAULT_LOG_DIR


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def capture(
    pipeline: str,
    exit_code: int,
    timed_out: bool,
    started_at: datetime,
    finished_at: datetime,
    tags: List[str] | None = None,
    notes: str = "",
    log_dir: str = DEFAULT_LOG_DIR,
) -> RunLog:
    """Build a RunLog from run metadata and save it to disk."""
    duration = (finished_at - started_at).total_seconds()
    entry = RunLog(
        pipeline=pipeline,
        started_at=_fmt(started_at),
        finished_at=_fmt(finished_at),
        exit_code=exit_code,
        timed_out=timed_out,
        duration=duration,
        tags=tags or [],
        notes=notes,
    )
    save_log(entry, log_dir=log_dir)
    return entry


def capture_from_result(result, pipeline: str, started_at: datetime,
                        finished_at: datetime, tags: List[str] | None = None,
                        log_dir: str = DEFAULT_LOG_DIR) -> RunLog:
    """Convenience wrapper: accept a RunResult-like object."""
    return capture(
        pipeline=pipeline,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        started_at=started_at,
        finished_at=finished_at,
        tags=tags,
        log_dir=log_dir,
    )
