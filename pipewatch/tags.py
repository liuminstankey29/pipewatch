"""Tag filtering utilities for pipeline runs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class TagFilter:
    """Matches runs that carry ALL of the required tags."""
    required: list[str] = field(default_factory=list)

    def matches(self, tags: Iterable[str]) -> bool:
        """Return True when every required tag is present in *tags*."""
        if not self.required:
            return True
        tag_set = set(tags)
        return all(t in tag_set for t in self.required)


def parse_tags(raw: str | None) -> list[str]:
    """Split a comma-separated tag string into a sorted, deduplicated list.

    >>> parse_tags("etl,nightly,etl")
    ['etl', 'nightly']
    >>> parse_tags(None)
    []
    """
    if not raw:
        return []
    return sorted(set(t.strip() for t in raw.split(",") if t.strip()))


def tags_from_config(cfg_tags: list[str] | None) -> list[str]:
    """Normalise the tags list stored in a Config object."""
    if not cfg_tags:
        return []
    return sorted(set(cfg_tags))


def format_tags(tags: Iterable[str]) -> str:
    """Return a human-readable tag string, e.g. ``[etl] [nightly]``."""
    parts = [f"[{t}]" for t in sorted(tags)]
    return " ".join(parts) if parts else ""
