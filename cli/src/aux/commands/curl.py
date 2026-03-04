"""Fetch command - CLI wrapper for fetch kernel (agent-optimised HTTP fetch)."""

from __future__ import annotations

import argparse
import json

from aux.output import format_output
from aux.plans import CurlPlan, get_schema, parse_plan


CAPABILITY: dict = {
    "name": "curl",
    "description": "Agent-optimised HTTP fetch with progressive disclosure and HTML-to-text extraction.",
    "category": "network",
    "intent_signals": [
        "fetch a URL and return its content",
        "make an HTTP GET or POST request",
        "retrieve web page or API response for agent consumption",
    ],
    "requires": ["urls"],
    "optional_deps": [],
    "compose_with": [],
    "mutates": False,
    "schema_cmd": "aux curl --schema",
}


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the fetch subcommand."""
    parser = subparsers.add_parser(
        "curl",
        help="Agent-optimised HTTP fetch with progressive disclosure",
        description="""
Fetch URLs and return clean, chunked content optimised for agent consumption.

HTML is extracted to plain text or Markdown before the agent sees it.
JSON responses are pretty-printed. Progressive disclosure lets agents
request successive chunks by incrementing --offset.

Simple usage:
  aux curl https://example.com                         # auto mode, first chunk
  aux curl https://example.com --mode text             # explicit text extraction
  aux curl https://example.com --offset 20000          # next chunk
  aux curl https://api.example.com/data --mode json    # JSON formatting

Plan usage:
  aux curl --plan '<json>'
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Simple mode: URL as positional argument
    parser.add_argument(
        "url",
        nargs="?",
        help="URL to fetch (simple mode; use --plan for batch/advanced)",
    )
    parser.add_argument(
        "--method",
        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
        default="GET",
        help="HTTP method (default: GET)",
    )
    parser.add_argument(
        "--header",
        action="append",
        dest="headers",
        default=[],
        metavar="KEY:VALUE",
        help="Request header as KEY:VALUE (repeatable)",
    )
    parser.add_argument(
        "--body",
        type=str,
        default=None,
        help="Request body for POST/PUT/PATCH",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "text", "markdown", "json", "raw"],
        default="auto",
        help="Content extraction mode (default: auto — detect from Content-Type)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Character offset for progressive disclosure (default: 0)",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=20_000,
        help="Characters to return from offset (default: 20000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--no-follow-redirects",
        action="store_true",
        help="Do not follow HTTP redirects",
    )

    # Plan mode
    parser.add_argument(
        "--plan",
        type=str,
        help="Full plan as JSON (overrides other options)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print JSON schema for --plan and exit",
    )

    parser.set_defaults(func=cmd_curl)


def cmd_curl(args: argparse.Namespace) -> int:
    """Execute fetch command."""
    # Schema mode
    if args.schema:
        schema = get_schema("curl")
        print(json.dumps(schema, indent=2))
        return 0

    # Build plan
    if args.plan:
        try:
            plan = parse_plan(args.plan, CurlPlan)
        except ValueError as e:
            print(format_output({"error": str(e)}))
            return 1
    else:
        if not args.url:
            print(format_output({"error": "URL required (positional) or use --plan"}))
            return 1

        # Parse KEY:VALUE headers
        headers: dict[str, str] = {}
        for h in args.headers:
            if ":" not in h:
                print(format_output({"error": f"Invalid header (expected KEY:VALUE): {h!r}"}))
                return 1
            key, _, value = h.partition(":")
            headers[key.strip()] = value.strip()

        try:
            plan = CurlPlan(
                urls=[args.url],
                method=args.method,
                headers=headers,
                body=args.body,
                mode=args.mode,
                offset=args.offset,
                length=args.length,
                timeout=args.timeout,
                follow_redirects=not args.no_follow_redirects,
            )
        except Exception as e:
            print(format_output({"error": str(e)}))
            return 1

    # Execute kernel (import here to surface ImportError clearly)
    try:
        from aux.kernels.curl import curl_kernel
    except ImportError as e:
        print(format_output({"error": str(e)}))
        return 1

    result = curl_kernel(plan)

    # Format output
    output = _format_result(result)
    print(format_output(output))

    has_errors = any(r.error is not None for r in result.responses)
    return 1 if has_errors else 0


def _format_result(result) -> dict:
    """Format CurlResult for CLI output."""
    def _response_dict(r) -> dict:
        return {
            "url": r.url,
            "status": r.status,
            "content_type": r.content_type,
            "mode": r.mode,
            "offset": r.offset,
            "length": r.length,
            "chars_returned": r.chars_returned,
            "total_chars": r.total_chars,
            "has_more": r.has_more,
            "next_offset": r.next_offset,
            "content": r.content,
            "error": r.error,
        }

    if len(result.responses) == 1:
        return _response_dict(result.responses[0])

    return {
        "summary": result.summary,
        "results": [_response_dict(r) for r in result.responses],
    }
