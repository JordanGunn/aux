"""Shared types, HTTP client factory, mode detection, and chunking for fetch kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aux.plans.schemas import CurlPlan


@dataclass
class CurlResponse:
    """Result for a single fetched URL."""

    url: str
    status: int | None
    content_type: str | None
    mode: str
    offset: int
    length: int
    chars_returned: int
    total_chars: int
    has_more: bool
    next_offset: int | None
    content: str
    error: str | None = None


@dataclass
class CurlResult:
    """Aggregated result from curl_kernel."""

    responses: list[CurlResponse] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


def detect_mode(content_type: str | None, declared_mode: str) -> str:
    """Resolve the actual extraction mode from Content-Type and declared mode.

    Args:
        content_type: Value of the Content-Type response header (may be None).
        declared_mode: Mode from the plan ("auto", "text", "markdown", "json", "raw").

    Returns:
        Resolved mode: "text", "markdown", "json", or "raw".
    """
    if declared_mode != "auto":
        return declared_mode

    if not content_type:
        return "raw"

    ct = content_type.lower().split(";")[0].strip()

    if ct in ("text/html", "application/xhtml+xml"):
        return "text"
    if ct == "application/json" or ct.endswith("+json"):
        return "json"
    if ct.startswith("text/"):
        return "raw"

    return "raw"


def chunk(content: str, offset: int, length: int) -> tuple[str, bool, int | None]:
    """Slice content for progressive disclosure.

    Args:
        content: Full extracted text.
        offset: Character offset to start from.
        length: Maximum characters to return.

    Returns:
        Tuple of (sliced_text, has_more, next_offset).
        next_offset is None when has_more is False.
    """
    total = len(content)
    start = min(offset, total)
    end = min(start + length, total)
    sliced = content[start:end]
    has_more = end < total
    next_offset = end if has_more else None
    return sliced, has_more, next_offset


def make_client(plan: "CurlPlan"):  # -> httpx.Client
    """Build an httpx.Client configured from plan options.

    Raises:
        ImportError: If httpx is not installed.
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "httpx is required for 'aux curl'. "
            "Install it with: pip install 'aux-skills[curl]'"
        ) from e

    return httpx.Client(
        timeout=plan.timeout,
        follow_redirects=plan.follow_redirects,
    )
