"""CLI helpers for hook configuration."""
from __future__ import annotations

import argparse
from typing import Optional

from pipewatch.hooks import HookConfig, hooks_from_config


def add_hook_args(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_argument_group("hooks")
    grp.add_argument(
        "--pre-hook",
        metavar="CMD",
        action="append",
        default=[],
        help="Command to run before the pipeline (repeatable).",
    )
    grp.add_argument(
        "--post-hook",
        metavar="CMD",
        action="append",
        default=[],
        help="Command to run after the pipeline (repeatable).",
    )
    grp.add_argument(
        "--failure-hook",
        metavar="CMD",
        action="append",
        default=[],
        help="Command to run when the pipeline fails (repeatable).",
    )
    grp.add_argument(
        "--hook-timeout",
        type=int,
        default=None,
        metavar="SECS",
        help="Timeout in seconds for each hook command.",
    )


def hooks_from_args(args: argparse.Namespace) -> HookConfig:
    return HookConfig(
        pre=args.pre_hook or [],
        post=args.post_hook or [],
        on_failure=args.failure_hook or [],
        timeout=args.hook_timeout if args.hook_timeout is not None else 30,
    )


def resolve_hooks(args: argparse.Namespace, cfg_dict: Optional[dict] = None) -> HookConfig:
    """Merge CLI hook args over config-file hooks."""
    base = hooks_from_config(cfg_dict or {})
    cli = hooks_from_args(args)
    return HookConfig(
        pre=cli.pre or base.pre,
        post=cli.post or base.post,
        on_failure=cli.on_failure or base.on_failure,
        timeout=args.hook_timeout if args.hook_timeout is not None else base.timeout,
    )
