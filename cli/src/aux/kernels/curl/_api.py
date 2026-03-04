"""JSON/API extraction path: parse → format."""

from __future__ import annotations

import json


def extract_json(body: str) -> tuple[str, str | None]:
    """Parse and pretty-format a JSON response body.

    Args:
        body: Raw response body string.

    Returns:
        Tuple of (formatted_content, warning).
        warning is None on success, or a message string if JSON parsing failed.
    """
    try:
        parsed = json.loads(body)
        return json.dumps(parsed, indent=2, ensure_ascii=False), None
    except json.JSONDecodeError as e:
        return body, f"JSON parse failed ({e}); returning raw body"
