"""Fetch kernel — agent-optimised HTTP fetch with progressive disclosure.

Public API:
    curl_kernel(plan) -> CurlResult
    CurlResponse      — per-URL result dataclass
    CurlResult        — aggregated result dataclass
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from aux.kernels.curl._api import extract_json
from aux.kernels.curl._common import (
    CurlResponse,
    CurlResult,
    chunk,
    detect_mode,
    make_client,
)
from aux.kernels.curl._html import extract_html

if TYPE_CHECKING:
    from aux.plans.schemas import CurlPlan

__all__ = ["curl_kernel", "CurlResponse", "CurlResult"]


def curl_kernel(plan: "CurlPlan", *, parallelism: int = 4) -> CurlResult:
    """Execute HTTP fetches for all URLs in the plan.

    Args:
        plan: Validated CurlPlan instance.
        parallelism: Max concurrent worker threads.

    Returns:
        CurlResult with per-URL responses and aggregate summary.
    """
    try:
        client = make_client(plan)
    except ImportError as e:
        # Return a single error result if httpx is missing
        err_response = CurlResponse(
            url=plan.urls[0] if plan.urls else "",
            status=None,
            content_type=None,
            mode=plan.mode,
            offset=plan.offset,
            length=plan.length,
            chars_returned=0,
            total_chars=0,
            has_more=False,
            next_offset=None,
            content="",
            error=str(e),
        )
        return CurlResult(
            responses=[err_response],
            summary={"total": len(plan.urls), "success": 0, "errors": len(plan.urls)},
        )

    responses: list[CurlResponse] = []

    with client:
        with ThreadPoolExecutor(max_workers=min(parallelism, len(plan.urls))) as executor:
            futures = {
                executor.submit(_curl_one, url, plan, client): url
                for url in plan.urls
            }
            for future in as_completed(futures):
                responses.append(future.result())

    # Stable output: sort by URL
    responses.sort(key=lambda r: r.url)

    success = sum(1 for r in responses if r.error is None)
    errors = len(responses) - success

    summary: dict = {"total": len(responses), "success": success, "errors": errors}

    return CurlResult(responses=responses, summary=summary)


def _curl_one(url: str, plan: "CurlPlan", client) -> CurlResponse:
    """Fetch and process a single URL."""
    import httpx

    try:
        response = client.request(
            method=plan.method,
            url=url,
            headers=plan.headers or {},
            content=plan.body.encode() if plan.body else None,
        )
    except httpx.TimeoutException as e:
        return _error_response(url, plan, f"Request timed out: {e}")
    except httpx.RequestError as e:
        return _error_response(url, plan, f"Request error: {e}")

    content_type = response.headers.get("content-type")
    resolved_mode = detect_mode(content_type, plan.mode)

    try:
        body = response.text
    except Exception as e:
        return _error_response(
            url, plan, f"Failed to decode response body: {e}",
            response.status_code, content_type, resolved_mode,
        )

    # Extract content based on mode
    warning: str | None = None
    if resolved_mode in ("text", "markdown"):
        content = extract_html(body, resolved_mode)  # type: ignore[arg-type]
    elif resolved_mode == "json":
        content, warning = extract_json(body)
    else:
        content = body  # raw

    # Apply progressive disclosure chunking
    sliced, has_more, next_offset = chunk(content, plan.offset, plan.length)

    fetch_response = CurlResponse(
        url=url,
        status=response.status_code,
        content_type=content_type,
        mode=resolved_mode,
        offset=plan.offset,
        length=plan.length,
        chars_returned=len(sliced),
        total_chars=len(content),
        has_more=has_more,
        next_offset=next_offset,
        content=sliced,
        error=warning,
    )
    return fetch_response


def _error_response(
    url: str,
    plan: "CurlPlan",
    error: str,
    status: int | None = None,
    content_type: str | None = None,
    mode: str | None = None,
) -> CurlResponse:
    """Build a CurlResponse representing a failed request."""
    return CurlResponse(
        url=url,
        status=status,
        content_type=content_type,
        mode=mode or plan.mode,
        offset=plan.offset,
        length=plan.length,
        chars_returned=0,
        total_chars=0,
        has_more=False,
        next_offset=None,
        content="",
        error=error,
    )
