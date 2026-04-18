"""Utilities for redacting sensitive values from env/config before logging."""
from __future__ import annotations

import re
from typing import Dict, Iterable

_DEFAULT_PATTERNS: list[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_-]?key",
    r"(?i)auth",
    r"(?i)credential",
]

REDACTED = "***"


def _is_sensitive(key: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, key) for p in patterns)


def redact_dict(
    data: Dict[str, str],
    extra_patterns: Iterable[str] | None = None,
) -> Dict[str, str]:
    """Return a copy of *data* with sensitive values replaced by REDACTED."""
    patterns = list(_DEFAULT_PATTERNS) + list(extra_patterns or [])
    return {
        k: (REDACTED if _is_sensitive(k, patterns) else v)
        for k, v in data.items()
    }


def redact_str(text: str, values: Iterable[str]) -> str:
    """Replace each literal value in *values* inside *text* with REDACTED."""
    for val in values:
        if val:
            text = text.replace(val, REDACTED)
    return text


def sensitive_values(data: Dict[str, str], extra_patterns: Iterable[str] | None = None) -> list[str]:
    """Return the values that would be redacted from *data*."""
    patterns = list(_DEFAULT_PATTERNS) + list(extra_patterns or [])
    return [v for k, v in data.items() if _is_sensitive(k, patterns)]
