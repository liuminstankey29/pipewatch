"""Command-line interface for pipewatch.

Provides the `pipewatch` command for running and monitoring pipeline jobs
with optional Slack alerting on success or failure.
"""

import sys
import argparse
import logging
from pathlib import Path

from pipewatch.config import load, save, validate, Config
from pipewatch.monitor import run_pipeline

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a pipeline command and optionally alert via Slack."""
    config_path = Path(args.config) if args.config else None

    if config_path and config_path.exists():
        cfg = load(config_path)
        logger.debug("Loaded config from %s", config_path)
    else:
        cfg = Config()
        if args.webhook:
            cfg.slack_webhook_url = args.webhook
        if args.timeout:
            cfg.timeout_seconds = args.timeout
        if args.alert_on:
            cfg.alert_on = args.alert_on

    errors = validate(cfg)
    if errors:
        for err in errors:
            logger.error("Config error: %s", err)
        return 2

    pipeline_cmd = args.command
    logger.info("Starting pipeline: %s", " ".join(pipeline_cmd))

    result = run_pipeline(pipeline_cmd, cfg)

    status = "succeeded" if result.succeeded else "failed"
    logger.info(
        "Pipeline %s (exit_code=%s, elapsed=%.1fs)",
        status,
        result.exit_code,
        result.elapsed_seconds,
    )
    if result.timed_out:
        logger.warning("Pipeline timed out after %s seconds", cfg.timeout_seconds)

    return 0 if result.succeeded else 1


def cmd_init(args: argparse.Namespace) -> int:
    """Write a default config file to disk."""
    dest = Path(args.output)
    if dest.exists() and not args.force:
        logger.error("%s already exists. Use --force to overwrite.", dest)
        return 2
    cfg = Config()
    save(cfg, dest)
    logger.info("Config written to %s", dest)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Lightweight CLI monitor for long-running data pipeline jobs.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # pipewatch run
    run_parser = subparsers.add_parser("run", help="Run a pipeline command")
    run_parser.add_argument("command", nargs=argparse.REMAINDER, help="Pipeline command to execute")
    run_parser.add_argument("-c", "--config", metavar="FILE", help="Path to config YAML file")
    run_parser.add_argument("-w", "--webhook", metavar="URL", help="Slack webhook URL")
    run_parser.add_argument("-t", "--timeout", type=int, metavar="SECONDS", help="Timeout in seconds")
    run_parser.add_argument(
        "--alert-on",
        nargs="+",
        choices=["success", "failure"],
        metavar="EVENT",
        help="When to send Slack alerts (success, failure)",
    )
    run_parser.set_defaults(func=cmd_run)

    # pipewatch init
    init_parser = subparsers.add_parser("init", help="Generate a default config file")
    init_parser.add_argument("-o", "--output", default="pipewatch.yml", help="Output file path")
    init_parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing file")
    init_parser.set_defaults(func=cmd_init)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
