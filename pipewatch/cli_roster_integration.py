"""Integration helpers: resolve roster state for a running pipeline."""
from __future__ import annotations

import logging
from typing import Optional

from pipewatch.roster import Roster, RosterEntry, load_roster

log = logging.getLogger(__name__)


def resolve_entry(pipeline: str, state_dir: Optional[str]) -> Optional[RosterEntry]:
    """Return the RosterEntry for *pipeline*, or None if not registered."""
    if not state_dir:
        return None
    try:
        roster = load_roster(state_dir)
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not load roster from %s: %s", state_dir, exc)
        return None
    return roster.get(pipeline)


def is_pipeline_enabled(pipeline: str, state_dir: Optional[str]) -> bool:
    """Return True if the pipeline is registered and enabled (or not registered)."""
    entry = resolve_entry(pipeline, state_dir)
    if entry is None:
        return True  # unknown pipelines are allowed by default
    return entry.enabled


def roster_summary(state_dir: str) -> str:
    """Return a one-line summary of the roster for logging/display."""
    try:
        roster = load_roster(state_dir)
    except Exception as exc:  # noqa: BLE001
        return f"roster unavailable ({exc})"
    total = len(roster.all())
    active = len(roster.enabled())
    return f"{active}/{total} pipelines enabled"


def assert_pipeline_enabled(pipeline: str, state_dir: Optional[str]) -> None:
    """Raise RuntimeError if the pipeline is registered but disabled."""
    entry = resolve_entry(pipeline, state_dir)
    if entry is not None and not entry.enabled:
        raise RuntimeError(
            f"Pipeline '{pipeline}' is disabled in the roster. "
            "Enable it with: pipewatch roster toggle {pipeline} --enable"
        )
