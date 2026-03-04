"""mv kernel — deterministic filesystem move/rename via shutil.move."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MvMoveResult:
    src: str
    dst: str
    applied: bool = False
    backup_path: str | None = None
    conflict: bool = False
    error: str | None = None


@dataclass
class MvResult:
    moves: list[MvMoveResult]
    total_moves: int
    total_applied: int
    errors: list[str] = field(default_factory=list)


def mv_kernel(
    moves: list[tuple[Path, Path]],
    *,
    apply: bool = False,
    backup: bool = False,
    overwrite: bool = False,
) -> MvResult:
    """Execute or preview a batch of src→dst moves.

    Args:
        moves: List of (src, dst) Path pairs.
        apply: If False, dry-run only (validate but do not move).
        backup: Copy src to <src>.bak before moving (apply mode only).
        overwrite: Allow moving onto an existing destination.

    Returns:
        MvResult with per-move results and aggregated error list.
    """
    results: list[MvMoveResult] = []

    for src, dst in moves:
        result = MvMoveResult(src=str(src), dst=str(dst))

        # Validation (runs in both dry-run and apply)
        if not src.exists():
            result.error = f"source does not exist: {src}"
            results.append(result)
            continue

        if not dst.parent.exists():
            result.error = f"destination parent does not exist: {dst.parent}"
            results.append(result)
            continue

        if dst.exists() and not overwrite:
            result.conflict = True
            result.error = f"destination exists: {dst}"
            results.append(result)
            continue

        if not apply:
            # Dry-run: validation passed, no writes
            results.append(result)
            continue

        # Apply
        try:
            if backup:
                bak = Path(str(src) + ".bak")
                if src.is_dir():
                    shutil.copytree(str(src), str(bak))
                else:
                    shutil.copy2(str(src), str(bak))
                result.backup_path = str(bak)

            shutil.move(str(src), str(dst))
            result.applied = True
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)

        results.append(result)

    errors = [
        f"{r.src} → {r.dst}: {r.error}"
        for r in results
        if r.error
    ]

    return MvResult(
        moves=results,
        total_moves=len(results),
        total_applied=sum(1 for r in results if r.applied),
        errors=errors,
    )
