"""CLI helpers for concurrency limit policy."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.concurrency import ConcurrencyPolicy, _DEFAULT_STATE_DIR


def add_concurrency_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("concurrency")
    grp.add_argument(
        "--max-concurrent",
        type=int,
        default=0,
        metavar="N",
        help="Maximum simultaneous runs allowed (0 = unlimited)",
    )
    grp.add_argument(
        "--concurrency-state-dir",
        default=_DEFAULT_STATE_DIR,
        metavar="DIR",
        help="Directory to store concurrency state files",
    )


def policy_from_args(args: argparse.Namespace, pipeline: str = "default") -> ConcurrencyPolicy:
    return ConcurrencyPolicy(
        max_concurrent=args.max_concurrent,
        state_dir=args.concurrency_state_dir,
        pipeline=pipeline,
    )


def policy_from_config(cfg: dict, pipeline: str = "default") -> ConcurrencyPolicy:
    return ConcurrencyPolicy(
        max_concurrent=int(cfg.get("max_concurrent", 0)),
        state_dir=cfg.get("concurrency_state_dir", _DEFAULT_STATE_DIR),
        pipeline=pipeline,
    )


def resolve_concurrency(
    args: argparse.Namespace,
    cfg: Optional[dict],
    pipeline: str = "default",
) -> ConcurrencyPolicy:
    if args.max_concurrent:
        return policy_from_args(args, pipeline)
    if cfg:
        return policy_from_config(cfg, pipeline)
    return ConcurrencyPolicy(pipeline=pipeline)
