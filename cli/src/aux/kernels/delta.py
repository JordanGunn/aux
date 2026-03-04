"""Delta kernel - semantic git diff (symbols added/removed since a ref)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aux.util.subprocess import run_tool, which


@dataclass
class SymbolDiff:
    """Symbol-level diff between two versions of a file."""

    added: list[tuple[str, str]]      # (name, type) new in ref_to
    removed: list[tuple[str, str]]    # (name, type) present in ref_from, gone in ref_to
    unchanged: list[tuple[str, str]]  # (name, type) present in both


@dataclass
class FileDelta:
    """Delta info for a single changed file."""

    file: str               # abs path (resolved against root)
    language: str | None
    status: str             # "modified" | "added" | "deleted" | "renamed"
    additions: int          # raw git line additions
    deletions: int          # raw git line deletions
    symbols: SymbolDiff | None   # None if stat_only or tree-sitter absent


@dataclass
class DeltaResult:
    """Aggregated semantic git diff result."""

    ref_from: str
    ref_to: str             # "working tree" if ref_to was None
    files: list[FileDelta]
    summary: dict           # keys: files_changed, symbols_added/removed, lines_added/deleted
    errors: list[str] = field(default_factory=list)
    truncated: bool = False


def delta_kernel(
    root: Path,
    *,
    ref_from: str = "HEAD",
    ref_to: str | None = None,
    globs: list[str] | None = None,
    excludes: list[str] | None = None,
    language: str | None = None,
    semantic: bool = True,
    stat_only: bool = False,
    max_files: int | None = None,
) -> DeltaResult:
    """Compute semantic delta between two git refs.

    Args:
        root: Git repo root (or subdirectory)
        ref_from: Base ref (default: HEAD)
        ref_to: Target ref (None = working tree, staged + unstaged)
        globs: Filter changed files by glob pattern
        excludes: Exclude patterns
        language: Tree-sitter language override
        semantic: Attempt AST symbol diff (requires tree-sitter)
        stat_only: Skip symbol analysis, return only file+line counts
        max_files: Cap on files analyzed

    Returns:
        DeltaResult with per-file deltas and summary
    """
    ref_to_label = ref_to if ref_to is not None else "working tree"
    errors: list[str] = []

    # Check git availability
    if which("git") is None:
        return DeltaResult(
            ref_from=ref_from,
            ref_to=ref_to_label,
            files=[],
            summary={"files_changed": 0, "symbols_added": 0, "symbols_removed": 0,
                     "lines_added": 0, "lines_deleted": 0},
            errors=["git not found — install git and ensure it is in PATH"],
        )

    # Get changed files with status
    name_status_cmd = ["git", "diff", "--name-status", ref_from]
    if ref_to is not None:
        name_status_cmd.append(ref_to)

    ns_result = run_tool(name_status_cmd, cwd=root)
    if not ns_result.ok and ns_result.returncode != 0:
        err = ns_result.stderr.strip() or f"git diff failed (exit {ns_result.returncode})"
        return DeltaResult(
            ref_from=ref_from,
            ref_to=ref_to_label,
            files=[],
            summary={"files_changed": 0, "symbols_added": 0, "symbols_removed": 0,
                     "lines_added": 0, "lines_deleted": 0},
            errors=[err],
        )

    # Parse name-status output
    changed_files = _parse_name_status(ns_result.stdout)

    # Apply glob/exclude filters
    if globs or excludes:
        changed_files = _filter_files(changed_files, globs or [], excludes or [])

    # Get line stats via --numstat
    numstat_cmd = ["git", "diff", "--numstat", ref_from]
    if ref_to is not None:
        numstat_cmd.append(ref_to)

    ns_stat = run_tool(numstat_cmd, cwd=root)
    stat_map = _parse_numstat(ns_stat.stdout) if ns_stat.ok else {}

    # Determine if semantic analysis is possible
    ts_available = _treesitter_available()
    do_semantic = semantic and not stat_only
    if do_semantic and not ts_available:
        errors.append("tree-sitter not installed — falling back to stat-only mode. "
                      "Install with: pip install 'aux-skills[query]'")
        do_semantic = False

    # Cap files
    truncated = False
    if max_files is not None and len(changed_files) > max_files:
        changed_files = changed_files[:max_files]
        truncated = True

    # Build FileDelta list
    file_deltas: list[FileDelta] = []

    for rel_path, status in changed_files:
        abs_path = str((root / rel_path).resolve())
        lang = language or _detect_file_language(Path(rel_path))
        additions, deletions = stat_map.get(rel_path, (0, 0))

        symbols: SymbolDiff | None = None
        if do_semantic and lang is not None:
            sym_errors: list[str] = []
            symbols, sym_errors = _compute_symbol_diff(
                root=root,
                rel_path=rel_path,
                abs_path=abs_path,
                status=status,
                ref_from=ref_from,
                ref_to=ref_to,
                language=lang,
            )
            errors.extend(sym_errors)

        file_deltas.append(FileDelta(
            file=abs_path,
            language=lang,
            status=status,
            additions=additions,
            deletions=deletions,
            symbols=symbols,
        ))

    # Compute summary
    total_symbols_added = 0
    total_symbols_removed = 0
    for fd in file_deltas:
        if fd.symbols is not None:
            total_symbols_added += len(fd.symbols.added)
            total_symbols_removed += len(fd.symbols.removed)

    total_lines_added = sum(fd.additions for fd in file_deltas)
    total_lines_deleted = sum(fd.deletions for fd in file_deltas)

    summary = {
        "files_changed": len(file_deltas),
        "symbols_added": total_symbols_added,
        "symbols_removed": total_symbols_removed,
        "lines_added": total_lines_added,
        "lines_deleted": total_lines_deleted,
    }

    return DeltaResult(
        ref_from=ref_from,
        ref_to=ref_to_label,
        files=file_deltas,
        summary=summary,
        errors=errors,
        truncated=truncated,
    )


def _parse_name_status(output: str) -> list[tuple[str, str]]:
    """Parse git diff --name-status output.

    Returns list of (rel_path, status) tuples.
    Status: "modified" | "added" | "deleted" | "renamed"
    """
    results: list[tuple[str, str]] = []
    status_map = {"M": "modified", "A": "added", "D": "deleted"}

    for line in output.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        code = parts[0].strip()
        if code.startswith("R"):
            # Renamed: R100\told_path\tnew_path
            new_path = parts[2] if len(parts) > 2 else parts[1]
            results.append((new_path, "renamed"))
        elif code in status_map:
            results.append((parts[1], status_map[code]))

    return results


def _parse_numstat(output: str) -> dict[str, tuple[int, int]]:
    """Parse git diff --numstat output.

    Returns dict: rel_path -> (additions, deletions).
    Binary files show '-' which is mapped to 0.
    """
    result: dict[str, tuple[int, int]] = {}
    for line in output.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_str, del_str, path = parts[0], parts[1], parts[2]
        try:
            additions = int(add_str) if add_str != "-" else 0
            deletions = int(del_str) if del_str != "-" else 0
        except ValueError:
            continue
        result[path] = (additions, deletions)
    return result


def _filter_files(
    files: list[tuple[str, str]],
    globs: list[str],
    excludes: list[str],
) -> list[tuple[str, str]]:
    """Filter (rel_path, status) list by glob/exclude patterns."""
    import fnmatch

    filtered: list[tuple[str, str]] = []
    for rel_path, status in files:
        # Apply excludes first
        if any(fnmatch.fnmatch(rel_path, pat) for pat in excludes):
            continue
        # Apply includes (if any specified)
        if globs and not any(fnmatch.fnmatch(rel_path, pat) for pat in globs):
            continue
        filtered.append((rel_path, status))
    return filtered


def _compute_symbol_diff(
    root: Path,
    rel_path: str,
    abs_path: str,
    status: str,
    ref_from: str,
    ref_to: str | None,
    language: str,
) -> tuple[SymbolDiff | None, list[str]]:
    """Compute symbol-level diff for a single file.

    Returns (SymbolDiff, errors).
    """
    from aux.kernels.usages import DEFINITION_QUERIES

    errors: list[str] = []

    if language not in DEFINITION_QUERIES:
        return None, []

    # Get old content (from ref_from)
    old_content = ""
    if status != "added":
        old_result = run_tool(["git", "show", f"{ref_from}:{rel_path}"], cwd=root)
        if old_result.ok:
            old_content = old_result.stdout
        else:
            err = old_result.stderr.strip()
            errors.append(f"Could not retrieve {rel_path} at {ref_from}: {err}")

    # Get new content
    new_content = ""
    if status != "deleted":
        if ref_to is None:
            # Working tree
            abs_file = root / rel_path
            try:
                new_content = abs_file.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                errors.append(f"Could not read {rel_path}: {e}")
        else:
            new_result = run_tool(["git", "show", f"{ref_to}:{rel_path}"], cwd=root)
            if new_result.ok:
                new_content = new_result.stdout
            else:
                err = new_result.stderr.strip()
                errors.append(f"Could not retrieve {rel_path} at {ref_to}: {err}")

    # Extract symbols from each version
    old_symbols = _extract_symbols_from_content(old_content, language) if old_content else set()
    new_symbols = _extract_symbols_from_content(new_content, language) if new_content else set()

    added = sorted(new_symbols - old_symbols)
    removed = sorted(old_symbols - new_symbols)
    unchanged = sorted(old_symbols & new_symbols)

    return SymbolDiff(
        added=list(added),
        removed=list(removed),
        unchanged=list(unchanged),
    ), errors


def _extract_symbols_from_content(content: str, language: str) -> set[tuple[str, str]]:
    """Extract symbol (name, type) pairs from file content using tree-sitter."""
    import os
    import tempfile

    from aux.kernels.query import query_kernel
    from aux.kernels.usages import DEFINITION_QUERIES
    from aux.util.treesitter import load_language

    symbols: set[tuple[str, str]] = set()
    lang_obj = load_language(language)
    if lang_obj is None:
        return symbols

    queries = DEFINITION_QUERIES.get(language, [])

    # Write content to a temp file so query_kernel can process it
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=_lang_ext(language),
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        for query_str, symbol_type in queries:
            result = query_kernel(
                files=[Path(tmp_path)],
                query_str=query_str,
                language=language,
            )
            for match in result.matches:
                for cap in match.captures:
                    if cap.name == "name":
                        symbols.add((cap.text, symbol_type))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return symbols


def _lang_ext(language: str) -> str:
    """Get file extension for a language (for temp file creation)."""
    ext_map = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "go": ".go",
        "rust": ".rs",
        "java": ".java",
    }
    return ext_map.get(language, ".txt")


def _detect_file_language(fp: Path) -> str | None:
    """Detect language from file extension."""
    ext = fp.suffix.lower()
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
    }
    return ext_map.get(ext)


def _treesitter_available() -> bool:
    """Check if tree-sitter is importable."""
    try:
        import tree_sitter  # noqa: F401
        return True
    except ImportError:
        return False
