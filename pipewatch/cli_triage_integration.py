"""Integration helpers: wire triage into a run result and attach to history entries."""
from __future__ import annotations

from typing import Optional

from pipewatch.triage import TriageResult, triage_failure


def triage_run_result(result: object) -> Optional[TriageResult]:
    """Given a RunResult-like object, return a TriageResult if the run failed.

    Looks for: .exit_code, .timed_out, .stderr, .stdout attributes.
    Returns None when the run succeeded (exit_code == 0 and not timed_out).
    """
    exit_code: int = getattr(result, "exit_code", 0)
    timed_out: bool = getattr(result, "timed_out", False)

    if exit_code == 0 and not timed_out:
        return None

    stderr: str = getattr(result, "stderr", "") or ""
    stdout: str = getattr(result, "stdout", "") or ""

    return triage_failure(
        exit_code=exit_code,
        timed_out=timed_out,
        stderr=stderr,
        stdout=stdout,
    )


def attach_triage_to_entry(entry: object, triage: TriageResult) -> None:
    """Attach triage metadata to a HistoryEntry / RunLog dict or object in-place.

    If *entry* is a dict, keys ``triage_category`` and ``triage_confidence`` are
    added.  If it is an object with a ``meta`` dict attribute the same keys are
    stored there; otherwise attributes are set directly.
    """
    if isinstance(entry, dict):
        entry["triage_category"] = triage.category
        entry["triage_confidence"] = triage.confidence
        return

    meta = getattr(entry, "meta", None)
    if isinstance(meta, dict):
        meta["triage_category"] = triage.category
        meta["triage_confidence"] = triage.confidence
    else:
        entry.triage_category = triage.category  # type: ignore[attr-defined]
        entry.triage_confidence = triage.confidence  # type: ignore[attr-defined]


def triage_summary_line(triage: Optional[TriageResult]) -> str:
    """Return a short one-line string suitable for Slack messages or log output."""
    if triage is None:
        return ""
    return f"Triage: {triage.summary()}"
