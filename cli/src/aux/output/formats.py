"""Output formatting for aux commands."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any


class OutputFormat(Enum):
    """Output format options."""

    JSON = "json"
    TEXT = "text"
    SUMMARY = "summary"


@dataclass
class OutputConfig:
    """Configuration for output formatting."""

    format: OutputFormat = OutputFormat.JSON
    max_matches: int | None = None
    indent: int = 2


def get_output_config() -> OutputConfig:
    """Get output configuration from environment."""
    fmt_str = os.environ.get("AUX_OUTPUT", "json").lower()
    try:
        fmt = OutputFormat(fmt_str)
    except ValueError:
        fmt = OutputFormat.JSON

    max_matches_str = os.environ.get("AUX_MAX_MATCHES")
    max_matches = int(max_matches_str) if max_matches_str else None

    return OutputConfig(format=fmt, max_matches=max_matches)


def format_output(
    data: dict[str, Any],
    *,
    format: OutputFormat | None = None,
    indent: int = 2,
) -> str:
    """Format output data according to specified format.

    Args:
        data: Output data dictionary
        format: Output format (defaults to environment config)
        indent: JSON indent level

    Returns:
        Formatted string output
    """
    config = get_output_config()
    fmt = format or config.format

    if fmt == OutputFormat.JSON:
        return json.dumps(data, indent=indent, default=str)

    if fmt == OutputFormat.SUMMARY:
        return _format_summary(data)

    if fmt == OutputFormat.TEXT:
        return _format_text(data)

    return json.dumps(data, indent=indent, default=str)


def _format_summary(data: dict[str, Any]) -> str:
    """Format data as concise summary."""
    lines = []

    if "summary" in data:
        summary = data["summary"]
        if isinstance(summary, dict):
            for key, val in summary.items():
                lines.append(f"{key}: {val}")
        else:
            lines.append(str(summary))

    if "error" in data:
        lines.append(f"error: {data['error']}")

    return "\n".join(lines) if lines else json.dumps(data)


def _format_text(data: dict[str, Any]) -> str:
    """Format data as human-readable text."""
    lines = []

    if "results" in data:
        for result in data["results"]:
            if isinstance(result, dict):
                if "file" in result and "matches" in result:
                    lines.append(f"\n{result['file']}:")
                    for match in result["matches"]:
                        line_num = match.get("line", "?")
                        content = match.get("content", "")
                        lines.append(f"  {line_num}: {content}")
                elif "path" in result:
                    lines.append(result["path"])
                else:
                    lines.append(str(result))
            else:
                lines.append(str(result))

    if "error" in data:
        lines.append(f"error: {data['error']}")

    if not lines:
        return json.dumps(data, indent=2)

    return "\n".join(lines)
