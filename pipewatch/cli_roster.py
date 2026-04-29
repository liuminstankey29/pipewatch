"""CLI helpers for roster subcommands."""
from __future__ import annotations

import argparse
from typing import List, Optional

from pipewatch.roster import (
    Roster,
    RosterEntry,
    format_roster,
    load_roster,
    save_roster,
)


def add_roster_args(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="roster_cmd")

    reg = sub.add_parser("register", help="Register a pipeline")
    reg.add_argument("name", help="Pipeline name")
    reg.add_argument("--description", default="", help="Short description")
    reg.add_argument("--owner", default="", help="Owner name or team")
    reg.add_argument("--tag", dest="tags", action="append", default=[], metavar="TAG")
    reg.add_argument("--disabled", action="store_true", help="Register as disabled")

    sub.add_parser("list", help="List registered pipelines")

    rm = sub.add_parser("remove", help="Remove a pipeline from the roster")
    rm.add_argument("name", help="Pipeline name")

    tog = sub.add_parser("toggle", help="Enable or disable a pipeline")
    tog.add_argument("name", help="Pipeline name")
    tog.add_argument("--enable", action="store_true")
    tog.add_argument("--disable", action="store_true")


def handle_roster_cmd(args: argparse.Namespace, state_dir: str) -> int:
    roster = load_roster(state_dir)
    cmd = getattr(args, "roster_cmd", None)

    if cmd == "register":
        entry = RosterEntry(
            name=args.name,
            description=args.description,
            owner=args.owner,
            tags=args.tags,
            enabled=not args.disabled,
        )
        roster.register(entry)
        save_roster(roster, state_dir)
        print(f"Registered pipeline: {args.name}")
        return 0

    if cmd == "list":
        print(format_roster(roster))
        return 0

    if cmd == "remove":
        removed = roster.remove(args.name)
        if removed:
            save_roster(roster, state_dir)
            print(f"Removed pipeline: {args.name}")
            return 0
        print(f"Pipeline not found: {args.name}")
        return 1

    if cmd == "toggle":
        entry = roster.get(args.name)
        if entry is None:
            print(f"Pipeline not found: {args.name}")
            return 1
        if args.enable:
            entry.enabled = True
        elif args.disable:
            entry.enabled = False
        else:
            entry.enabled = not entry.enabled
        save_roster(roster, state_dir)
        state = "enabled" if entry.enabled else "disabled"
        print(f"Pipeline '{args.name}' is now {state}")
        return 0

    print("No roster subcommand given. Use --help.")
    return 1
