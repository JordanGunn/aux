"""Kernel functions for aux commands.

Kernels are pure functions that operate on data structures.
CLI commands are thin wrappers around kernels.
Composition happens at the kernel level for in-process pipelines.
"""

from aux.kernels.grep import grep_kernel, GrepMatch
from aux.kernels.find import find_kernel, FindEntry
from aux.kernels.diff import diff_kernel, DiffHunk
from aux.kernels.ls import ls_kernel, LsEntry

__all__ = [
    "grep_kernel",
    "GrepMatch",
    "find_kernel",
    "FindEntry",
    "diff_kernel",
    "DiffHunk",
    "ls_kernel",
    "LsEntry",
]
