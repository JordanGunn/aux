"""Path resolution utilities."""

from __future__ import annotations

from pathlib import Path


def resolve_path(path: str | Path) -> Path:
    """Resolve a path to absolute, expanding user and symlinks.

    Args:
        path: Path string or Path object

    Returns:
        Resolved absolute Path

    Raises:
        ValueError: If path doesn't exist
    """
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise ValueError(f"Path does not exist: {p}")
    return p


def resolve_globs(globs: list[str], root: Path) -> list[str]:
    """Normalize glob patterns for use with tools.

    Args:
        globs: List of glob patterns
        root: Root directory for relative patterns

    Returns:
        List of normalized glob patterns
    """
    normalized = []
    for glob in globs:
        # Already has wildcards, use as-is
        if "*" in glob or "?" in glob:
            normalized.append(glob)
        else:
            # Treat as literal path/prefix
            normalized.append(glob)
    return normalized


def make_relative(path: Path, root: Path) -> str:
    """Make a path relative to root if possible.

    Args:
        path: Path to make relative
        root: Root directory

    Returns:
        Relative path string, or absolute if not under root
    """
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
