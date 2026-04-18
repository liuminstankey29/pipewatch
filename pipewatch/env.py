"""Environment variable injection and masking for pipeline runs."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SECRET_PATTERN = re.compile(r"(token|secret|password|key|api)", re.IGNORECASE)
_MASK = "***"


@dataclass
class PipelineEnv:
    """Holds extra env vars to inject and tracks which keys are sensitive."""
    extras: Dict[str, str] = field(default_factory=dict)
    secret_keys: List[str] = field(default_factory=list)

    def build(self, base: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Merge extras on top of *base* (defaults to os.environ)."""
        env = dict(base if base is not None else os.environ)
        env.update(self.extras)
        return env

    def safe_repr(self) -> Dict[str, str]:
        """Return extras with secret values masked."""
        result: Dict[str, str] = {}
        for k, v in self.extras.items():
            if k in self.secret_keys or _SECRET_PATTERN.search(k):
                result[k] = _MASK
            else:
                result[k] = v
        return result


def parse_env_pairs(pairs: List[str]) -> Dict[str, str]:
    """Parse a list of 'KEY=VALUE' strings into a dict."""
    out: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid env pair (expected KEY=VALUE): {pair!r}")
        k, _, v = pair.partition("=")
        out[k.strip()] = v
    return out


def env_from_config(cfg_env: Optional[Dict[str, str]]) -> PipelineEnv:
    """Build a PipelineEnv from the 'env' section of a config dict."""
    extras = dict(cfg_env) if cfg_env else {}
    secrets = [k for k in extras if _SECRET_PATTERN.search(k)]
    return PipelineEnv(extras=extras, secret_keys=secrets)
