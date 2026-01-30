# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-01-29

### Added

- **Results section in README** with token consumption improvements
  - 47% reduction in context usage (182k → 98k tokens)
  - 98% reduction in search operations (200-300 scans → 6 targeted passes)
- **Quick Start section** in README with CLI examples
- `aux <skill> --schema` command for all skills (source of truth for plan schemas)
- `aux doctor` command to verify system dependencies

### Changed

- **CLI schema is now source of truth** — removed static schema/template JSON files
- Skills reorganized under `skills/` directory
- Updated all skill documentation to reference `aux <skill> --schema`
- Fixed wrapper scripts (`skill.sh`, `skill.ps1`) to match actual CLI interface

### Removed

- Static schema files (`*.schema.json`) — use `aux <skill> --schema` instead
- Static template files (`*.template.json`) — use CLI-generated schemas
- Legacy `bootstrap.sh` / `bootstrap.ps1` scripts

### Fixed

- **grep**: Pattern is now positional argument (not `--pattern` flag)
- **all skills**: Help text now matches actual CLI interface
- **find**: Support for `fdfind` binary name on Debian/Ubuntu
  - `fd-find` package installs as `fdfind` to avoid naming conflicts
  - Skill now checks for `fd` first, falls back to `fdfind`

## [0.1.0] - 2026-01-28

### Added

- Initial release of aux skills
- **grep** — Agent-assisted text search using ripgrep
- **find** — Agent-assisted file enumeration using fd
- **diff** — Deterministic git diff inspection
- **ls** — Deterministic directory state inspection
- Unified installation via `scripts/install.sh` and `scripts/install.ps1`
- JSON schemas for plans and receipts
- Reference documentation for agent navigation

[Unreleased]: https://github.com/JordanGunn/aux/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/JordanGunn/aux/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/JordanGunn/aux/releases/tag/v0.1.0
