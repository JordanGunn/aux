"""Diff kernel - file comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aux.util.subprocess import run_tool


@dataclass
class DiffHunk:
    """A single diff hunk."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str] = field(default_factory=list)


@dataclass
class DiffFile:
    """Diff result for a single file."""

    path_a: str
    path_b: str
    hunks: list[DiffHunk] = field(default_factory=list)
    binary: bool = False


@dataclass
class DiffResult:
    """Aggregated diff results."""

    files: list[DiffFile]
    total_files: int
    total_additions: int
    total_deletions: int
    errors: list[str] = field(default_factory=list)


def diff_kernel(
    path_a: Path,
    path_b: Path,
    *,
    context_lines: int = 3,
    ignore_whitespace: bool = False,
    ignore_case: bool = False,
    unified: bool = True,
) -> DiffResult:
    """Compare files or directories.

    Args:
        path_a: First path
        path_b: Second path
        context_lines: Context lines around changes
        ignore_whitespace: Ignore whitespace changes
        ignore_case: Ignore case differences
        unified: Use unified diff format

    Returns:
        DiffResult with comparison data
    """
    args = ["diff"]

    if unified:
        args.append(f"-U{context_lines}")
    else:
        args.extend(["-c", f"-C{context_lines}"])

    if ignore_whitespace:
        args.append("-w")

    if ignore_case:
        args.append("-i")

    # Recursive for directories
    if path_a.is_dir() and path_b.is_dir():
        args.append("-r")

    args.extend([str(path_a), str(path_b)])

    result = run_tool(args)

    # diff returns 0=same, 1=different, 2=error
    if result.returncode == 2:
        return DiffResult(
            files=[],
            total_files=0,
            total_additions=0,
            total_deletions=0,
            errors=[result.stderr.strip() if result.stderr else "diff error"],
        )

    files, additions, deletions = _parse_diff_output(result.stdout)

    return DiffResult(
        files=files,
        total_files=len(files),
        total_additions=additions,
        total_deletions=deletions,
    )


def _parse_diff_output(output: str) -> tuple[list[DiffFile], int, int]:
    """Parse unified diff output."""
    files: list[DiffFile] = []
    total_additions = 0
    total_deletions = 0

    current_file: DiffFile | None = None
    current_hunk: DiffHunk | None = None

    for line in output.split("\n"):
        if line.startswith("--- "):
            # New file diff
            if current_file:
                files.append(current_file)
            path_a = line[4:].split("\t")[0]
            current_file = DiffFile(path_a=path_a, path_b="")
            current_hunk = None

        elif line.startswith("+++ ") and current_file:
            path_b = line[4:].split("\t")[0]
            current_file.path_b = path_b

        elif line.startswith("@@ ") and current_file:
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            if current_hunk:
                current_file.hunks.append(current_hunk)

            try:
                parts = line.split(" ")
                old_part = parts[1]  # -old_start,old_count
                new_part = parts[2]  # +new_start,new_count

                old_start, old_count = _parse_hunk_range(old_part[1:])
                new_start, new_count = _parse_hunk_range(new_part[1:])

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                )
            except (IndexError, ValueError):
                current_hunk = None

        elif current_hunk is not None:
            current_hunk.lines.append(line)
            if line.startswith("+") and not line.startswith("+++"):
                total_additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                total_deletions += 1

        elif line.startswith("Binary files") and current_file:
            current_file.binary = True

    # Don't forget the last file/hunk
    if current_hunk and current_file:
        current_file.hunks.append(current_hunk)
    if current_file:
        files.append(current_file)

    return files, total_additions, total_deletions


def _parse_hunk_range(s: str) -> tuple[int, int]:
    """Parse hunk range like '10,5' or '10'."""
    if "," in s:
        parts = s.split(",")
        return int(parts[0]), int(parts[1])
    return int(s), 1
