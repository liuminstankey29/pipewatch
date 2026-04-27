"""CLI argument helpers for the sampling policy."""
from __future__ import annotations

import argparse

from pipewatch.sampling import SamplingPolicy


def add_sampling_args(parser: argparse.ArgumentParser) -> None:
    """Register --sample-rate on *parser*."""
    parser.add_argument(
        "--sample-rate",
        dest="sample_rate",
        type=float,
        default=None,
        metavar="RATE",
        help=(
            "Fraction of executions to run (0.0–1.0). "
            "E.g. 0.5 runs approximately half of all invocations. "
            "Default: 1.0 (always run)."
        ),
    )


def policy_from_args(args: argparse.Namespace) -> SamplingPolicy:
    rate = args.sample_rate if args.sample_rate is not None else 1.0
    return SamplingPolicy(rate=float(rate))


def policy_from_config(cfg) -> SamplingPolicy:
    rate = float(getattr(cfg, "sample_rate", None) or 1.0)
    return SamplingPolicy(rate=rate)


def resolve_sampling(args: argparse.Namespace, cfg) -> SamplingPolicy:
    if args.sample_rate is not None:
        return policy_from_args(args)
    return policy_from_config(cfg)
