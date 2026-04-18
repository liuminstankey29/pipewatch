"""CLI helpers for environment variable injection."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.env import PipelineEnv, env_from_config, parse_env_pairs
from pipewatch.config import Config


def add_env_args(parser: argparse.ArgumentParser) -> None:
    """Attach --env flags to *parser*."""
    parser.add_argument(
        "--env",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        dest="env_pairs",
        help="Extra environment variable injected into the pipeline process (repeatable).",
    )


def env_from_args(args: argparse.Namespace) -> PipelineEnv:
    """Build a PipelineEnv from CLI *args* alone."""
    pairs = getattr(args, "env_pairs", []) or []
    extras = parse_env_pairs(pairs)
    return PipelineEnv(extras=extras)


def resolve_env(args: argparse.Namespace, cfg: Optional[Config] = None) -> PipelineEnv:
    """Merge config-level env with CLI overrides (CLI wins)."""
    base = env_from_config(getattr(cfg, "env", None) if cfg else None)
    cli_pairs = getattr(args, "env_pairs", []) or []
    cli_extras = parse_env_pairs(cli_pairs)
    base.extras.update(cli_extras)
    # refresh secret detection after merge
    from pipewatch.env import _SECRET_PATTERN
    base.secret_keys = [k for k in base.extras if _SECRET_PATTERN.search(k)]
    return base
