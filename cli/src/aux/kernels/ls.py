"""Ls kernel - directory listing."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class LsEntry:
    """A directory entry."""

    name: str
    path: str
    type: Literal["file", "directory", "symlink", "other"]
    size: int
    modified: datetime | None = None
    permissions: str | None = None


@dataclass
class LsResult:
    """Directory listing result."""

    entries: list[LsEntry]
    total_entries: int
    total_size: int
    path: str
    errors: list[str]


def ls_kernel(
    path: Path,
    *,
    depth: int = 1,
    show_hidden: bool = False,
    show_size: bool = True,
    show_time: bool = False,
    sort_by: Literal["name", "size", "time"] = "name",
    max_entries: int | None = None,
) -> LsResult:
    """List directory contents.

    Args:
        path: Directory path
        depth: Recursion depth (1 = no recursion)
        show_hidden: Include hidden files
        show_size: Include file sizes
        show_time: Include modification times
        sort_by: Sort order
        max_entries: Maximum entries to return

    Returns:
        LsResult with directory entries
    """
    if not path.exists():
        return LsResult(
            entries=[],
            total_entries=0,
            total_size=0,
            path=str(path),
            errors=[f"Path does not exist: {path}"],
        )

    if not path.is_dir():
        return LsResult(
            entries=[],
            total_entries=0,
            total_size=0,
            path=str(path),
            errors=[f"Not a directory: {path}"],
        )

    entries: list[LsEntry] = []
    errors: list[str] = []
    total_size = 0

    try:
        entries = _scan_directory(
            path,
            path,
            depth,
            show_hidden,
            show_size,
            show_time,
        )
    except PermissionError as e:
        errors.append(f"Permission denied: {e}")
    except OSError as e:
        errors.append(f"OS error: {e}")

    # Calculate total size
    total_size = sum(e.size for e in entries)

    # Sort entries
    entries = _sort_entries(entries, sort_by)

    # Apply max_entries limit
    total_entries = len(entries)
    if max_entries and len(entries) > max_entries:
        entries = entries[:max_entries]

    return LsResult(
        entries=entries,
        total_entries=total_entries,
        total_size=total_size,
        path=str(path),
        errors=errors,
    )


def _scan_directory(
    root: Path,
    current: Path,
    depth: int,
    show_hidden: bool,
    show_size: bool,
    show_time: bool,
) -> list[LsEntry]:
    """Recursively scan directory."""
    entries: list[LsEntry] = []

    if depth < 1:
        return entries

    try:
        for item in current.iterdir():
            # Skip hidden files unless requested
            if not show_hidden and item.name.startswith("."):
                continue

            try:
                st = item.stat(follow_symlinks=False)

                # Determine type
                if stat.S_ISDIR(st.st_mode):
                    entry_type: Literal["file", "directory", "symlink", "other"] = "directory"
                elif stat.S_ISLNK(st.st_mode):
                    entry_type = "symlink"
                elif stat.S_ISREG(st.st_mode):
                    entry_type = "file"
                else:
                    entry_type = "other"

                # Get relative path from root
                rel_path = str(item.relative_to(root))

                entry = LsEntry(
                    name=item.name,
                    path=rel_path,
                    type=entry_type,
                    size=st.st_size if show_size else 0,
                    modified=datetime.fromtimestamp(st.st_mtime) if show_time else None,
                    permissions=stat.filemode(st.st_mode) if show_time else None,
                )
                entries.append(entry)

                # Recurse into directories
                if entry_type == "directory" and depth > 1:
                    entries.extend(_scan_directory(
                        root,
                        item,
                        depth - 1,
                        show_hidden,
                        show_size,
                        show_time,
                    ))

            except (PermissionError, OSError):
                continue

    except PermissionError:
        pass

    return entries


def _sort_entries(entries: list[LsEntry], sort_by: str) -> list[LsEntry]:
    """Sort entries by specified criteria."""
    if sort_by == "size":
        return sorted(entries, key=lambda e: e.size, reverse=True)
    elif sort_by == "time":
        return sorted(
            entries,
            key=lambda e: e.modified or datetime.min,
            reverse=True,
        )
    else:  # name
        return sorted(entries, key=lambda e: e.path.lower())
