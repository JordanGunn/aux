"""Capabilities command - emit structured skill registry for agent discovery."""

from __future__ import annotations

import argparse
import json

CAPABILITY: dict = {
    "name": "capabilities",
    "description": "Emit structured skill registry for agent discovery and routing.",
    "category": "meta",
    "intent_signals": [
        "discover all available skills",
        "choose the right skill for an ambiguous task",
        "bootstrap a new agent with no prior context",
    ],
    "requires": [],
    "optional_deps": [],
    "compose_with": [],
    "mutates": False,
    "schema_cmd": None,
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the capabilities subcommand."""
    parser = subparsers.add_parser(
        "capabilities",
        help="Emit structured skill registry for agent discovery",
        description="""
Emit a compact JSON registry of all available skills.

Designed for agent bootstrap: run this once to understand what skills exist,
then fetch --schema for the selected skill before constructing a plan.

Usage:
  aux capabilities               # Full registry (JSON)
  aux capabilities --format names  # Skill names only (lightweight)
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--format",
        choices=["json", "names"],
        default="json",
        help="Output format: 'json' for full registry, 'names' for skill name list (default: json)",
    )

    parser.set_defaults(func=cmd_capabilities)


def cmd_capabilities(args: argparse.Namespace) -> int:
    """Execute capabilities command."""
    from aux import __version__
    from aux.commands import curl, delta, deps, files, find, prune, rename, replace, robert, search, usages

    modules = [files, search, find, replace, rename, curl, usages, prune, deps, delta, robert]
    registry = [m.CAPABILITY for m in modules if hasattr(m, "CAPABILITY")]

    if args.format == "names":
        print(json.dumps([s["name"] for s in registry], indent=2))
        return 0

    output = {
        "version": __version__,
        "skills": registry,
        "composition_note": (
            "Fetch --schema for each selected skill before constructing a plan. "
            "Write skills (mutates=true) require a dry-run confirmation before --apply."
        ),
    }
    print(json.dumps(output, indent=2))
    return 0
