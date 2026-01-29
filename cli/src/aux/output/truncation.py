"""Output truncation utilities."""

from __future__ import annotations

from typing import Any


def truncate_results(
    results: list[Any],
    max_items: int | None,
    *,
    count_key: str | None = None,
) -> tuple[list[Any], dict[str, Any]]:
    """Truncate results list and return truncation metadata.

    Args:
        results: List of results to potentially truncate
        max_items: Maximum items to return (None = no limit)
        count_key: If results are dicts, count by this nested key

    Returns:
        Tuple of (truncated_results, truncation_info)
    """
    total = len(results)

    if max_items is None or total <= max_items:
        return results, {"truncated": False, "total": total, "returned": total}

    truncated = results[:max_items]

    return truncated, {
        "truncated": True,
        "total": total,
        "returned": max_items,
        "omitted": total - max_items,
    }


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count for text.

    Uses simple heuristic: ~4 characters per token.
    """
    return len(text) // 4


def truncate_to_tokens(
    results: list[Any],
    max_tokens: int,
    *,
    serialize_fn: callable = str,
) -> tuple[list[Any], dict[str, Any]]:
    """Truncate results to fit within token budget.

    Args:
        results: List of results
        max_tokens: Maximum tokens for output
        serialize_fn: Function to serialize results for token counting

    Returns:
        Tuple of (truncated_results, truncation_info)
    """
    truncated = []
    token_count = 0
    total = len(results)

    for item in results:
        item_text = serialize_fn(item)
        item_tokens = estimate_tokens(item_text)

        if token_count + item_tokens > max_tokens:
            break

        truncated.append(item)
        token_count += item_tokens

    returned = len(truncated)

    if returned == total:
        return results, {"truncated": False, "total": total, "returned": total}

    return truncated, {
        "truncated": True,
        "total": total,
        "returned": returned,
        "omitted": total - returned,
        "estimated_tokens": token_count,
    }
