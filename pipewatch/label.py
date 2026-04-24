"""Pipeline run labelling — attach arbitrary key/value labels to runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def matches(self, filters: Dict[str, str]) -> bool:
        """Return True when every filter key/value is present in this set."""
        return all(self.labels.get(k) == v for k, v in filters.items())

    def to_dict(self) -> Dict[str, str]:
        return dict(self.labels)

    def format(self) -> str:
        if not self.labels:
            return ""
        return " ".join(f"{k}={v}" for k, v in sorted(self.labels.items()))


def parse_labels(pairs: Optional[List[str]]) -> LabelSet:
    """Parse a list of 'key=value' strings into a LabelSet."""
    if not pairs:
        return LabelSet()
    result: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid label (expected key=value): {pair!r}")
        k, _, v = pair.partition("=")
        k = k.strip()
        if not k:
            raise ValueError(f"Label key must not be empty: {pair!r}")
        result[k] = v.strip()
    return LabelSet(result)


def labels_from_config(cfg_labels: Optional[Dict[str, str]]) -> LabelSet:
    """Build a LabelSet from a config dict (already parsed key/value pairs)."""
    if not cfg_labels:
        return LabelSet()
    return LabelSet(dict(cfg_labels))


def filter_from_labels(pairs: Optional[List[str]]) -> Dict[str, str]:
    """Parse filter pairs into a plain dict for use with LabelSet.matches."""
    ls = parse_labels(pairs)
    return ls.to_dict()
