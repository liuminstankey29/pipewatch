"""Integration helpers: attach labels to RunLog / History entries."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipewatch.label import LabelSet


def apply_labels_to_entry(entry: Dict[str, Any], labels: LabelSet) -> Dict[str, Any]:
    """Return a copy of *entry* with a 'labels' key set from *labels*."""
    updated = dict(entry)
    updated["labels"] = labels.to_dict()
    return updated


def filter_entries_by_labels(
    entries: List[Dict[str, Any]],
    filters: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Return only entries whose labels satisfy *filters*."""
    if not filters:
        return list(entries)
    result = []
    for entry in entries:
        raw = entry.get("labels") or {}
        ls = LabelSet(raw)
        if ls.matches(filters):
            result.append(entry)
    return result


def label_summary(entries: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Aggregate all distinct values seen for each label key across *entries*."""
    summary: Dict[str, set] = {}
    for entry in entries:
        for k, v in (entry.get("labels") or {}).items():
            summary.setdefault(k, set()).add(v)
    return {k: sorted(v) for k, v in sorted(summary.items())}
