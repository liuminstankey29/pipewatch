"""CLI helpers for trend analysis."""
from __future__ import annotations
import argparse
from pipewatch.trend import analyze_trend, TrendResult
from pipewatch.history import RunHistory
from pipewatch.config import Config


def add_trend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--trend", action="store_true", default=False,
                        help="Analyse duration trend for the pipeline.")
    parser.add_argument("--trend-window", type=int, default=10, metavar="N",
                        help="Number of recent successful runs to include (default: 10).")
    parser.add_argument("--trend-degrade", type=float, default=5.0, metavar="S",
                        help="Slope threshold (s/run) to flag as degrading (default: 5.0).")
    parser.add_argument("--trend-improve", type=float, default=-5.0, metavar="S",
                        help="Slope threshold (s/run) to flag as improving (default: -5.0).")


def trend_from_args(args: argparse.Namespace, pipeline: str, history: RunHistory) -> TrendResult | None:
    if not getattr(args, "trend", False):
        return None
    return analyze_trend(
        history,
        pipeline,
        window=args.trend_window,
        degrade_threshold=args.trend_degrade,
        improve_threshold=args.trend_improve,
    )


def trend_from_config(cfg: Config, pipeline: str, history: RunHistory) -> TrendResult | None:
    trend_cfg = (cfg.raw.get("trend") or {}) if hasattr(cfg, "raw") else {}
    if not trend_cfg.get("enabled", False):
        return None
    return analyze_trend(
        history,
        pipeline,
        window=int(trend_cfg.get("window", 10)),
        degrade_threshold=float(trend_cfg.get("degrade_threshold", 5.0)),
        improve_threshold=float(trend_cfg.get("improve_threshold", -5.0)),
    )
