"""Utility helpers — no internal imports, pure leaf module."""


def flatten(data: list[list]) -> list:
    """Flatten one level of nesting."""
    return [item for sublist in data for item in sublist]


def chunk(data: list, size: int) -> list[list]:
    """Split a list into fixed-size chunks."""
    return [data[i:i + size] for i in range(0, len(data), size)]
