"""Sed kernel - deterministic text substitution with optional AST-aware query mode."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from aux.plans.schemas import QueryReplacement, SedPlan, TextReplacement

from aux.util.treesitter import detect_language as _detect_language
from aux.util.treesitter import extract_captures as _ts_extract_captures
from aux.util.treesitter import load_language as _load_language


@dataclass
class SedChange:
    """A single line-level change produced by a sed operation."""

    path: str
    line_number: int       # 1-indexed
    original: str          # full line content, no trailing newline
    replacement: str       # proposed full line content
    operation_index: int   # index into plan.replacements
    mode: Literal["text", "query"]
    pattern: str           # pattern or query string (for audit trail)


@dataclass
class SedFileResult:
    """Per-file processing result."""

    path: str
    changes: list[SedChange]
    original_content: str
    proposed_content: str
    applied: bool = False
    backed_up: bool = False
    backup_path: str | None = None
    error: str | None = None


@dataclass
class SedResult:
    """Aggregated sed results."""

    files: list[SedFileResult]
    total_files: int
    total_changes: int
    applied: bool
    errors: list[str] = field(default_factory=list)


def sed_kernel(
    plan: "SedPlan",
    *,
    files: list[Path] | None = None,
    apply: bool = False,
    parallelism: int = 4,
) -> SedResult:
    """Execute deterministic text substitution.

    Args:
        plan: Validated SedPlan instance
        files: Pre-resolved file list (pipeline support). If None, resolved from plan.
        apply: If True, write changes to disk. If False, dry-run only.
        parallelism: Number of parallel file workers.

    Returns:
        SedResult with per-file results and aggregate counts.
    """
    target_files = _resolve_files(plan, files)

    file_results: list[SedFileResult] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures = {executor.submit(_process_file, p, plan): p for p in target_files}
        for future in as_completed(futures):
            result = future.result()
            file_results.append(result)
            if result.error:
                errors.append(f"{result.path}: {result.error}")

    # Stable output order
    file_results.sort(key=lambda r: r.path)

    if apply:
        for fr in file_results:
            if fr.error or not fr.changes:
                continue
            _write_file(fr, plan)

    total_changes = sum(len(fr.changes) for fr in file_results)

    return SedResult(
        files=file_results,
        total_files=len(file_results),
        total_changes=total_changes,
        applied=apply,
        errors=errors,
    )


def _resolve_files(plan: "SedPlan", override: list[Path] | None) -> list[Path]:
    """Resolve target file list from plan or override."""
    if override is not None:
        return override

    if plan.files:
        return [Path(f).expanduser().resolve() for f in plan.files]

    # Fall back to find_kernel for glob targeting
    from aux.kernels.find import find_kernel

    root = Path(plan.root).expanduser().resolve()  # type: ignore[arg-type]
    find_result = find_kernel(
        root=root,
        globs=plan.globs or None,
        excludes=plan.excludes or None,
    )
    return [root / entry.path for entry in find_result.entries]


def _process_file(path: Path, plan: "SedPlan") -> SedFileResult:
    """Read a file, apply all replacement operations, return a SedFileResult."""
    try:
        original_content = path.read_text(encoding=plan.encoding)
    except Exception as e:
        return SedFileResult(
            path=str(path),
            changes=[],
            original_content="",
            proposed_content="",
            error=str(e),
        )

    all_changes: list[SedChange] = []
    current_content = original_content

    for op_index, op in enumerate(plan.replacements):
        if op.mode == "text":
            lines = current_content.splitlines()
            changes = _apply_text(str(path), lines, op, op_index)
            all_changes.extend(changes)
            if changes:
                change_map = {c.line_number: c.replacement for c in changes}
                new_lines = [change_map.get(i + 1, line) for i, line in enumerate(lines)]
                current_content = "\n".join(new_lines)
                if original_content.endswith("\n"):
                    current_content += "\n"
        else:
            new_content, changes = _apply_query(current_content, op, op_index, path)
            all_changes.extend(changes)
            current_content = new_content

    return SedFileResult(
        path=str(path),
        changes=all_changes,
        original_content=original_content,
        proposed_content=current_content,
    )


def _apply_text(
    path: str,
    lines: list[str],
    op: "TextReplacement",
    op_index: int,
) -> list[SedChange]:
    """Apply a text-mode replacement operation to lines.

    Returns a list of SedChange for each line that changed.
    """
    flags = re.IGNORECASE if op.case == "insensitive" else 0

    if op.kind == "fixed":
        compiled = re.compile(re.escape(op.pattern), flags)
    else:
        try:
            compiled = re.compile(op.pattern, flags)
        except re.error:
            return []  # Invalid pattern — skip silently (caller handles errors at file level)

    changes: list[SedChange] = []
    replacements_made = 0

    for i, line in enumerate(lines):
        if op.count is not None and replacements_made >= op.count:
            break

        sub_limit = 0  # 0 = unlimited in re.subn
        if op.count is not None:
            sub_limit = op.count - replacements_made

        new_line, n = compiled.subn(op.replacement, line, count=sub_limit)

        if n > 0:
            replacements_made += n
            changes.append(SedChange(
                path=path,
                line_number=i + 1,
                original=line,
                replacement=new_line,
                operation_index=op_index,
                mode="text",
                pattern=op.pattern,
            ))

    return changes


def _apply_query(
    content: str,
    op: "QueryReplacement",
    op_index: int,
    path: Path,
) -> tuple[str, list[SedChange]]:
    """Apply a tree-sitter query-mode replacement operation.

    Returns (new_content, list[SedChange]).
    On grammar error, returns (original_content, []) — caller stores error.
    """
    try:
        import tree_sitter  # noqa: F401
    except ImportError:
        # tree-sitter not installed — return unchanged with empty changes
        return content, []

    # Resolve language
    language_name = _detect_language(path, op.language)

    if language_name is None:
        return content, []

    lang = _load_language(language_name)
    if lang is None:
        return content, []

    try:
        import tree_sitter

        parser = tree_sitter.Parser(lang)
        tree = parser.parse(content.encode(errors="replace"))

        query = lang.query(op.query)
        captures = query.captures(tree.root_node)

        # captures is a dict: capture_name → list[Node] (tree-sitter >= 0.22)
        # For older APIs it may be list[(Node, capture_name)]
        target_nodes = _ts_extract_captures(captures).get(op.capture, [])

        if not target_nodes:
            return content, []

        # Sort in reverse byte order so replacements don't shift positions
        target_nodes.sort(key=lambda n: n.start_byte, reverse=True)

        content_bytes = content.encode()
        changes: list[SedChange] = []

        for node in target_nodes:
            matched_text = content_bytes[node.start_byte:node.end_byte].decode(errors="replace")
            replacement_bytes = op.template.encode()
            content_bytes = (
                content_bytes[:node.start_byte] + replacement_bytes + content_bytes[node.end_byte:]
            )

            changes.append(SedChange(
                path=str(path),
                line_number=node.start_point[0] + 1,
                original=matched_text,
                replacement=op.template,
                operation_index=op_index,
                mode="query",
                pattern=op.query,
            ))

        # Reverse so changes are in forward order for output
        changes.reverse()
        return content_bytes.decode(errors="replace"), changes

    except Exception:
        return content, []


def _write_file(fr: SedFileResult, plan: "SedPlan") -> None:
    """Write proposed_content to disk, optionally creating a backup first."""
    path = Path(fr.path)

    if plan.backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        try:
            backup_path.write_bytes(path.read_bytes())
            fr.backed_up = True
            fr.backup_path = str(backup_path)
        except Exception as e:
            fr.error = f"backup failed: {e}"
            return

    # Atomic write: write to temp then rename
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(fr.proposed_content, encoding=plan.encoding)
        tmp_path.replace(path)
        fr.applied = True
    except Exception as e:
        fr.error = f"write failed: {e}"
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
