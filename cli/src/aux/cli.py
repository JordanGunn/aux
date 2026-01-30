"""Entry point for the aux CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from aux import __version__
from aux.commands import diff, find, grep, ls, scan
from aux.util.doctor import run_doctor

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="aux",
        description="AUx - Agentic Unix Skills CLI",
        epilog="""
Commands:
  grep    Search patterns in files (ripgrep)
  find    Locate files by name/glob (fd)
  diff    Compare files or directories
  ls      List directory contents with metadata
  scan    Composite: find files → grep patterns (pipeline)
  doctor  Verify system dependencies

Invocation modes:
  Simple:  aux grep "pattern" --root /path --glob "*.py"
  Plan:    aux grep --plan '<json>'

Environment:
  AUX_OUTPUT=json|text|summary    Output format (default: json)
  AUX_MAX_MATCHES=1000            Truncation limit
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"aux {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    # Register subcommands
    grep.register_parser(subparsers)
    find.register_parser(subparsers)
    diff.register_parser(subparsers)
    ls.register_parser(subparsers)
    scan.register_parser(subparsers)

    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Verify system dependencies (rg, fd, git, diff)",
        description="Check that required system tools are installed and accessible.",
    )
    doctor_parser.set_defaults(func=cmd_doctor)

    return parser


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run the doctor command."""
    results = run_doctor()
    print(json.dumps(results, indent=2))
    return 0 if results["ok"] else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
