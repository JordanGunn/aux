"""Pydantic schemas for aux command plans."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Pattern(BaseModel):
    """A search pattern with kind indicator."""

    kind: Literal["regex", "fixed"] = "regex"
    value: str


class GrepPlan(BaseModel):
    """Plan schema for grep command."""

    root: str = Field(..., description="Search root directory")
    patterns: list[Pattern] = Field(..., description="Patterns to search for")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    mode: Literal["regex", "fixed"] = Field(default="regex", description="Default pattern mode")
    case: Literal["smart", "sensitive", "insensitive"] = Field(
        default="smart", description="Case sensitivity"
    )
    context_lines: int = Field(default=0, ge=0, description="Context lines around matches")
    hidden: bool = Field(default=False, description="Search hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_matches: int | None = Field(default=None, ge=1, description="Maximum matches to return")


class FindPlan(BaseModel):
    """Plan schema for find command."""

    root: str = Field(..., description="Search root directory")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    type: Literal["file", "directory", "any"] = Field(default="file", description="Entry type")
    max_depth: int | None = Field(default=None, ge=1, description="Maximum depth")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(default=None, ge=1, description="Maximum results")


class DiffPlan(BaseModel):
    """Plan schema for diff command."""

    path_a: str = Field(..., description="First path (file or directory)")
    path_b: str = Field(..., description="Second path (file or directory)")
    context_lines: int = Field(default=3, ge=0, description="Context lines")
    ignore_whitespace: bool = Field(default=False, description="Ignore whitespace changes")
    ignore_case: bool = Field(default=False, description="Ignore case differences")
    unified: bool = Field(default=True, description="Unified diff format")


class LsPlan(BaseModel):
    """Plan schema for ls command."""

    path: str = Field(..., description="Directory path")
    depth: int = Field(default=1, ge=1, description="Recursion depth")
    show_hidden: bool = Field(default=False, description="Show hidden files")
    show_size: bool = Field(default=True, description="Show file sizes")
    show_time: bool = Field(default=False, description="Show modification times")
    sort_by: Literal["name", "size", "time"] = Field(default="name", description="Sort order")
    max_entries: int | None = Field(default=None, ge=1, description="Maximum entries")


class ScanPlan(BaseModel):
    """Plan schema for scan command (composite find → grep)."""

    root: str = Field(..., description="Search root directory")
    surface: FindPlan = Field(..., description="Surface discovery phase (find)")
    search: GrepPlan = Field(..., description="Content search phase (grep)")
