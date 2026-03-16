"""Entry point for the aux CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from aux import __version__
from aux.commands import capabilities, curl, delta, deps, files, find, prune, rename, replace, robert, search, usages
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
  files         Enumerate files by name/glob (fd)
  search        Hierarchical pipeline: find files → grep patterns [→ tree-sitter AST]
  find          Read-only tree-sitter structural search (AST-aware)
  usages        Symbol cross-reference: definitions + references in one call
  prune         Tiered dead code candidate audit (advisory — requires human verification)
  deps          Module dependency graph: coupling metrics, cycles, blast radius
  delta         Semantic git diff: files changed + symbols added/removed since a ref
  robert        Robert C. Martin package design metrics (coupling, abstractness, main sequence)
  replace       Replace a string everywhere in a codebase (dry-run + apply)
  rename        Move/rename files or directories (dry-run + apply)
  curl          Agent-optimised HTTP fetch with progressive disclosure
  capabilities  Emit structured skill registry for agent discovery
  doctor        Verify system dependencies

Invocation modes:
  Simple:  aux files --root /path --glob "*.py"
  Plan:    aux files --plan '<json>'

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
    files.register_parser(subparsers)
    search.register_parser(subparsers)
    find.register_parser(subparsers)
    replace.register_parser(subparsers)
    rename.register_parser(subparsers)
    curl.register_parser(subparsers)
    usages.register_parser(subparsers)
    prune.register_parser(subparsers)
    deps.register_parser(subparsers)
    delta.register_parser(subparsers)
    robert.register_parser(subparsers)
    capabilities.register_parser(subparsers)

    # Doctor command
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Verify system dependencies (rg, fd)",
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
