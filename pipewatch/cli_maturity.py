"""CLI helpers for the pipeline maturity feature."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.maturity import MaturityResult, score_pipeline
from pipewatch.history import RunHistory
from pipewatch.config import Config


def add_maturity_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("maturity")
    grp.add_argument(
        "--maturity",
        action="store_true",
        default=False,
        help="Print maturity score after the run.",
    )
    grp.add_argument(
        "--maturity-window",
        type=int,
        default=30,
        metavar="N",
        help="Number of recent runs to include in the score (default: 30).",
    )


def window_from_args(args: argparse.Namespace) -> int:
    return int(getattr(args, "maturity_window", 30))


def window_from_config(cfg: Config) -> int:
    return int(cfg.get("maturity_window", 30))


def resolve_maturity(
    args: argparse.Namespace,
    cfg: Optional[Config] = None,
) -> int:
    """Return the effective window size, preferring CLI args over config."""
    cli_window = getattr(args, "maturity_window", None)
    if cli_window is not None and cli_window != 30:
        return int(cli_window)
    if cfg is not None:
        return window_from_config(cfg)
    return window_from_args(args)


def evaluate_and_print(
    pipeline: str,
    history: RunHistory,
    window: int = 30,
) -> MaturityResult:
    """Score *pipeline* and print a summary line; return the result."""
    result = score_pipeline(history, pipeline, window=window)
    print(result.message)
    return result
