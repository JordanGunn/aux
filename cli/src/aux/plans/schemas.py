"""Pydantic schemas for aux command plans."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator


class Pattern(BaseModel):
    """A search pattern with kind indicator."""

    kind: Literal["regex", "fixed"] = "regex"
    value: str


class GrepPlan(BaseModel):
    """Plan schema for grep kernel (internal use; not an agent-facing command)."""

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


class FilesPlan(BaseModel):
    """Plan schema for files command (enumerate files in a directory tree)."""

    root: str = Field(..., description="Search root directory")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    type: Literal["file", "directory", "any"] = Field(default="file", description="Entry type")
    max_depth: int | None = Field(default=None, ge=1, description="Maximum depth")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(default=None, ge=1, description="Maximum results")


class StructurePlan(BaseModel):
    """Tier-3 tree-sitter query for search pipeline."""

    query: str = Field(..., description="Tree-sitter query string")
    language: str | None = Field(
        default=None, description="Language override (auto-detected if None)"
    )
    max_matches: int | None = Field(default=None, ge=1, description="Maximum structural matches")


class SearchPlan(BaseModel):
    """Plan schema for search command (fd → rg [→ tree-sitter] pipeline)."""

    root: str = Field(..., description="Search root directory")
    surface: FilesPlan = Field(..., description="Tier 1: file name/glob surface reduction (fd)")
    search: GrepPlan = Field(..., description="Tier 2: content pattern match (rg)")
    structure: StructurePlan | None = Field(
        default=None, description="Tier 3 (optional): AST structural match (tree-sitter)"
    )
    result_mode: Literal["matches", "files"] = Field(
        default="matches",
        description=(
            "Output granularity for two-tier results. "
            "'matches' (default): one entry per matched line. "
            "'files': one entry per matched file with match count — no line content."
        ),
    )


class TextReplacement(BaseModel):
    """A text-mode replacement operation (Python re module)."""

    mode: Literal["text"] = "text"
    pattern: str = Field(..., description="Regex or fixed-string pattern to find")
    replacement: str = Field(
        ..., description="Replacement string (supports regex backreferences)"
    )
    kind: Literal["regex", "fixed"] = Field(default="regex", description="Pattern kind")
    case: Literal["smart", "sensitive", "insensitive"] = Field(
        default="smart", description="Case sensitivity (smart=case-sensitive)"
    )
    count: int | None = Field(
        default=None, ge=1, description="Max substitutions per file (None=unlimited)"
    )


class QueryReplacement(BaseModel):
    """A tree-sitter query-mode replacement operation."""

    mode: Literal["query"] = "query"
    language: str | None = Field(
        default=None, description="Language name (auto-detected from extension if None)"
    )
    query: str = Field(..., description="Tree-sitter query string")
    capture: str = Field(..., description="Capture name whose matched text will be replaced")
    template: str = Field(..., description="Replacement text (plain string, not a format template)")


SedReplacement = Annotated[
    Union[TextReplacement, QueryReplacement],
    Field(discriminator="mode"),
]


class ReplacePlan(BaseModel):
    """Plan schema for replace command (focused fixed-string identifier rename).

    Simpler than SedPlan: one old string, one new string, one scope.
    Designed for Haiku-tier agents — no discriminated unions, no regex mode selection.
    """

    old: str = Field(..., description="Exact string to find (literal, not a regex)")
    new: str = Field(..., description="Replacement string")
    files: list[str] = Field(default_factory=list, description="Explicit file paths to process")
    root: str | None = Field(default=None, description="Root directory for glob targeting")
    globs: list[str] = Field(default_factory=list, description="Include globs (requires root)")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    backup: bool = Field(default=False, description="Write .bak backup before modifying each file")
    encoding: str = Field(default="utf-8", description="File encoding")

    @model_validator(mode="after")
    def require_files_or_root(self) -> "ReplacePlan":
        if not self.files and not self.root:
            raise ValueError("Either 'files' or 'root' must be provided")
        return self


class RenameRule(BaseModel):
    """A filename substitution rule applied to discovered file basenames."""

    find: str = Field(..., description="Literal string to find in filename")
    replace: str = Field(..., description="Replacement string")
    regex: bool = Field(default=False, description="Treat 'find' as a Python regex pattern")


class MovePair(BaseModel):
    """A single src→dst move operation."""

    src: str = Field(..., description="Source path (file or directory)")
    dst: str = Field(..., description="Destination path (absolute or relative to cwd)")


class RenamePlan(BaseModel):
    """Plan schema for rename command (filesystem move/rename with dry-run gate).

    Two modes (exactly one must be provided):
      - Explicit mode: provide 'moves' list of {src, dst} pairs.
      - Discovery mode: provide 'root' + 'rules' (and optionally 'globs'/'excludes');
        the command discovers matching files via fd and applies filename substitutions
        to generate the moves list internally.
    """

    # Explicit mode
    moves: list[MovePair] | None = Field(
        default=None, min_length=1, description="Src→dst pairs (explicit mode)"
    )

    # Discovery mode
    root: str | None = Field(default=None, description="Root directory for discovery (discovery mode)")
    globs: list[str] = Field(default_factory=list, description="Include globs (requires root)")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    rules: list[RenameRule] | None = Field(
        default=None, min_length=1, description="Filename substitution rules (discovery mode)"
    )

    # Shared
    backup: bool = Field(default=False, description="Copy src to <src>.bak before moving")
    overwrite: bool = Field(default=False, description="Allow overwriting existing destination")

    @model_validator(mode="after")
    def require_moves_or_rules(self) -> "RenamePlan":
        has_explicit = self.moves is not None
        has_discovery = self.root is not None and self.rules is not None
        if not has_explicit and not has_discovery:
            raise ValueError(
                "Either 'moves' (explicit mode) or 'root' + 'rules' (discovery mode) must be provided"
            )
        if has_explicit and has_discovery:
            raise ValueError("Provide either 'moves' or 'root'+'rules', not both")
        if self.root is None and (self.globs or self.excludes):
            raise ValueError("'globs' and 'excludes' require 'root'")
        return self


class SedPlan(BaseModel):
    """Plan schema for sed kernel (agent-assisted deterministic text substitution)."""

    files: list[str] = Field(default_factory=list, description="Explicit file paths to process")
    root: str | None = Field(default=None, description="Root directory for glob targeting")
    globs: list[str] = Field(default_factory=list, description="Include globs (requires root)")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    replacements: list[SedReplacement] = Field(
        ..., min_length=1, description="Replacement operations applied in order (min 1)"
    )
    backup: bool = Field(default=False, description="Write .bak backup before modifying each file")
    encoding: str = Field(default="utf-8", description="File encoding")

    @model_validator(mode="after")
    def require_files_or_root(self) -> "SedPlan":
        if not self.files and not self.root:
            raise ValueError("Either 'files' or 'root' must be provided")
        return self


class FindPlan(BaseModel):
    """Plan schema for find command (read-only tree-sitter structural search)."""

    query: str = Field(..., description="Tree-sitter query string")
    files: list[str] = Field(default_factory=list, description="Explicit file paths")
    root: str | None = Field(default=None, description="Root directory for glob targeting")
    globs: list[str] = Field(default_factory=list, description="Include globs (requires root)")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    language: str | None = Field(
        default=None, description="Language override (auto-detected from extension if None)"
    )
    max_matches: int | None = Field(default=None, ge=1, description="Maximum total matches")

    @model_validator(mode="after")
    def require_files_or_root(self) -> "FindPlan":
        if not self.files and not self.root:
            raise ValueError("Either 'files' or 'root' must be provided")
        return self


class UsagesPlan(BaseModel):
    """Plan schema for usages command (symbol cross-reference)."""

    root: str = Field(..., description="Search root directory")
    symbol: str = Field(..., description="Exact symbol name (literal string, not regex)")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    language: str | None = Field(
        default=None, description="Tree-sitter language override for definition detection"
    )
    definitions: bool = Field(
        default=True, description="Include AST definition tagging (requires tree-sitter)"
    )
    hidden: bool = Field(default=False, description="Search hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(default=None, ge=1, description="Maximum total results")


class PrunePlan(BaseModel):
    """Plan schema for prune command (tiered dead code candidate audit)."""

    root: str = Field(..., description="Search root directory")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    scope: list[Literal["files", "symbols"]] = Field(
        default_factory=lambda: ["symbols"],
        description="Analysis scopes: 'symbols' (tree-sitter) and/or 'files' (text-only)",
    )
    language: str | None = Field(
        default=None, description="Tree-sitter language override for symbols scope"
    )
    min_name_length: int = Field(
        default=4, ge=1, description="Skip symbols/stems shorter than this"
    )
    max_refs: int = Field(
        default=0, ge=0, description="Flag candidates with <= N external refs (0 = zero-ref only)"
    )
    hidden: bool = Field(default=False, description="Search hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_symbols: int | None = Field(
        default=None, ge=1, description="Cap on symbols analyzed (performance safety valve)"
    )


class DepsPlan(BaseModel):
    """Plan schema for deps command (module dependency graph analysis)."""

    root: str = Field(..., description="Search root directory")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    target: str | None = Field(
        default=None,
        description="Focus on one file (rel or abs path); None = full graph mode",
    )
    language: str | None = Field(
        default=None, description="Tree-sitter language override (auto-detected if None)"
    )
    max_depth: int | None = Field(
        default=None, ge=1, description="Transitive depth limit (None = unlimited)"
    )
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(
        default=None, ge=1, description="Cap on files in output"
    )


class DeltaPlan(BaseModel):
    """Plan schema for delta command (semantic git diff)."""

    root: str = Field(..., description="Git repo root (or subdirectory)")
    ref_from: str = Field(default="HEAD", description="Base ref")
    ref_to: str | None = Field(
        default=None, description="Target ref (None = working tree, staged + unstaged)"
    )
    globs: list[str] = Field(default_factory=list, description="Filter changed files by glob")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    language: str | None = Field(
        default=None, description="Tree-sitter language override"
    )
    semantic: bool = Field(default=True, description="Attempt AST symbol diff (requires tree-sitter)")
    stat_only: bool = Field(
        default=False, description="Skip symbol analysis, return only file and line counts"
    )
    max_files: int | None = Field(default=None, ge=1, description="Cap on files analyzed")


class RobertPlan(BaseModel):
    """Plan schema for robert command (package design metrics)."""

    root: str = Field(..., description="Search root directory")
    language: str = Field(..., description="Language to analyze: 'go' or 'python'")
    globs: list[str] = Field(default_factory=list, description="Include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(default=None, ge=1, description="Cap on packages in output")
    include_main: bool = Field(
        default=False,
        description="Go only: include 'package main' packages in analysis",
    )


class CcxPlan(BaseModel):
    """Plan schema for ccx command (cyclomatic + cognitive complexity)."""

    root: str = Field(..., description="Search root directory")
    languages: list[str] = Field(
        default_factory=list,
        description="Subset of supported languages to analyze (empty = all supported)",
    )
    globs: list[str] = Field(
        default_factory=list,
        description="Override include globs (otherwise derived from languages)",
    )
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(
        default=None, ge=1, description="Cap on functions in output (post-sort)"
    )
    min_ccx: int = Field(
        default=1, ge=1, description="Filter — only return functions with ccx >= this value"
    )


class CkPlan(BaseModel):
    """Plan schema for ck command (Chidamber & Kemerer class metrics)."""

    root: str = Field(..., description="Search root directory")
    languages: list[str] = Field(
        default_factory=list,
        description="Subset of supported languages to analyze (empty = all supported)",
    )
    globs: list[str] = Field(default_factory=list, description="Override include globs")
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(
        default=None, ge=1, description="Cap on classes in output"
    )


class HotspotsPlan(BaseModel):
    """Plan schema for hotspots command (churn-weighted complexity)."""

    root: str = Field(
        ...,
        description="Repository root (can be a subdirectory of the git repo)",
    )
    globs: list[str] = Field(default_factory=list, description="File patterns to include")
    excludes: list[str] = Field(default_factory=list, description="File patterns to exclude")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    since: str | None = Field(
        default="14 days ago",
        description=(
            "Git log window start (git-style: '14 days ago', '2025-01-01', "
            "'all'/'unbounded' for full history). Default is 14d — tuned for "
            "agentic code generation where architectural damage from file "
            "growth accumulates in days, not months. Widen to '90 days ago' "
            "or 'all' for human-pace repos."
        ),
    )
    until: str | None = Field(default=None, description="Git log window end")
    min_commits: int = Field(
        default=2, ge=1, description="Minimum commit count to include a file"
    )
    max_results: int | None = Field(
        default=None, ge=1, description="Cap the ranked result list (post-sort)"
    )
    hotspot_percentile: float = Field(
        default=0.75,
        ge=0.5,
        le=0.99,
        description="Percentile cutoff for hotspot quadrant classification",
    )


class HalsteadPlan(BaseModel):
    """Plan schema for halstead command (Halstead Software Science metrics)."""

    root: str = Field(..., description="Search root directory")
    languages: list[str] = Field(
        default_factory=list,
        description="Subset of supported languages to analyze (empty = all supported)",
    )
    globs: list[str] = Field(
        default_factory=list,
        description="Override include globs (otherwise derived from languages)",
    )
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(
        default=None, ge=1, description="Cap on functions in output (post-sort)"
    )
    min_volume: float = Field(
        default=0, ge=0, description="Filter — only return functions with volume >= this value"
    )


class NpathPlan(BaseModel):
    """Plan schema for npath command (NPATH acyclic execution path count)."""

    root: str = Field(..., description="Search root directory")
    languages: list[str] = Field(
        default_factory=list,
        description="Subset of supported languages to analyze (empty = all supported)",
    )
    globs: list[str] = Field(
        default_factory=list,
        description="Override include globs (otherwise derived from languages)",
    )
    excludes: list[str] = Field(default_factory=list, description="Exclude globs")
    hidden: bool = Field(default=False, description="Include hidden files")
    no_ignore: bool = Field(default=False, description="Don't respect gitignore")
    max_results: int | None = Field(
        default=None, ge=1, description="Cap on functions in output (post-sort)"
    )
    min_npath: int = Field(
        default=1, ge=1, description="Filter — only return functions with npath >= this value"
    )


class CurlPlan(BaseModel):
    """Plan schema for curl command (agent-optimised HTTP fetch with progressive disclosure)."""

    urls: list[str] = Field(..., min_length=1, description="URLs to fetch (min 1; batch supported)")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        default="GET", description="HTTP method"
    )
    headers: dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: str | None = Field(
        default=None, description="Request body for POST/PUT/PATCH (must be None for GET/DELETE)"
    )

    # Content mode — if "auto", detected from Content-Type header
    mode: Literal["auto", "text", "markdown", "json", "raw"] = Field(
        default="auto",
        description=(
            "Content extraction mode. auto=detect from Content-Type, "
            "text=clean plain text (trafilatura), markdown=HTML→Markdown, "
            "json=pretty-print JSON, raw=no processing"
        ),
    )

    # Progressive disclosure
    offset: int = Field(default=0, ge=0, description="Character offset into extracted content")
    length: int = Field(
        default=20_000, ge=100, description="Characters to return from offset (default: 20000)"
    )

    # Request options
    timeout: float = Field(default=30.0, ge=1.0, le=300.0, description="Request timeout in seconds")
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")

    @model_validator(mode="after")
    def body_only_for_write_methods(self) -> "CurlPlan":
        if self.body is not None and self.method in ("GET", "DELETE"):
            raise ValueError(f"'body' must be None for {self.method} requests")
        return self
