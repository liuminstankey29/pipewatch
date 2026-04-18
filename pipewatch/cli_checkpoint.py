"""CLI helpers for checkpoint subcommands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from pipewatch.checkpoint import Checkpoint, clear_checkpoint, load_checkpoint, save_checkpoint


def add_checkpoint_args(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="checkpoint_cmd")

    show = sub.add_parser("show", help="Show current checkpoint for a pipeline")
    show.add_argument("pipeline", help="Pipeline name")
    show.add_argument("--dir", default=None, help="Checkpoint directory")

    clear = sub.add_parser("clear", help="Clear checkpoint for a pipeline")
    clear.add_argument("pipeline", help="Pipeline name")
    clear.add_argument("--dir", default=None, help="Checkpoint directory")

    setp = sub.add_parser("set", help="Manually set a checkpoint step")
    setp.add_argument("pipeline", help="Pipeline name")
    setp.add_argument("step", help="Step name")
    setp.add_argument("--meta", default=None, help="JSON metadata string")
    setp.add_argument("--dir", default=None, help="Checkpoint directory")


def handle_checkpoint_cmd(args: argparse.Namespace) -> int:
    directory = Path(args.dir) if getattr(args, "dir", None) else None
    cmd = getattr(args, "checkpoint_cmd", None)

    if cmd == "show":
        cp = load_checkpoint(args.pipeline, directory)
        if cp is None:
            print(f"No checkpoint for '{args.pipeline}'.")
            return 1
        print(json.dumps(cp.to_dict(), indent=2))
        return 0

    if cmd == "clear":
        removed = clear_checkpoint(args.pipeline, directory)
        if removed:
            print(f"Checkpoint cleared for '{args.pipeline}'.")
        else:
            print(f"No checkpoint found for '{args.pipeline}'.")
        return 0

    if cmd == "set":
        meta = json.loads(args.meta) if getattr(args, "meta", None) else {}
        cp = Checkpoint(pipeline=args.pipeline, step=args.step, metadata=meta)
        path = save_checkpoint(cp, directory)
        print(f"Checkpoint saved to {path}.")
        return 0

    print("No checkpoint subcommand given.")
    return 1
