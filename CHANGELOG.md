# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `docs/` folder with skill documentation
  - `.INDEX.md` — Documentation index
  - `GREP.md` — grep skill documentation with examples
  - `FIND.md` — find skill documentation
  - `DIFF.md` — diff skill documentation
  - `LS.md` — ls skill documentation
- `CONTRIBUTING.md` — Contribution guidelines
- `CHANGELOG.md` — This changelog

### Fixed

- **find**: Support for `fdfind` binary name on Debian/Ubuntu
  - `fd-find` package installs as `fdfind` to avoid naming conflicts
  - Skill now checks for `fd` first, falls back to `fdfind`
  - Updated validation messages with clearer install instructions

## [0.1.0] - 2026-01-28

### Added

- Initial release of aux skills
- **grep** — Agent-assisted text search using ripgrep
- **find** — Agent-assisted file enumeration using fd
- **diff** — Deterministic git diff inspection
- **ls** — Deterministic directory state inspection
- Bootstrap scripts (`bootstrap.sh`, `bootstrap.ps1`) for each skill
- JSON schemas for plans and receipts
- Reference documentation for agent navigation

[Unreleased]: https://github.com/JordanGunn/aux/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JordanGunn/aux/releases/tag/v0.1.0
