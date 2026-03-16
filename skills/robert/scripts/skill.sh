#!/usr/bin/env bash
# robert skill - Robert C. Martin package design metrics
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
robert - Robert C. Martin package design metrics (coupling, abstractness, main sequence)

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute package design metrics analysis

Usage (run):
  skill.sh run --root <path> --language <go|python> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --language <go|python>       Language to analyze (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-results <n>            Max packages in output
  --include-main               Go only: include 'package main' packages

Examples:
  skill.sh run --root ./src --language python
  skill.sh run --root ./src --language go --include-main
  echo '{"root":"/path","language":"go"}' | skill.sh run --stdin

Execution backend: aux robert (aux-skills CLI)
EOF
}

cmd_init() {
    local refs_dir="$SKILL_DIR/references"
    local idx=1

    # Emit TOC header first
    echo "# References"
    echo ""
    for f in "$refs_dir"/[0-9][0-9]_*.md; do
        [[ "$(basename "$f")" == "00_ROUTER.md" ]] && continue
        [[ -f "$f" ]] || continue
        local name desc
        name=$(basename "$f" .md | sed 's/^[0-9]*_//')
        desc=$(grep -m1 '^description:' "$f" 2>/dev/null | sed 's/^description:[[:space:]]*//' || echo "")
        echo "${idx}. **${name}** — ${desc}"
        idx=$((idx + 1))
    done
    echo ""
    echo "---"
    echo ""

    # Emit content
    for f in "$refs_dir"/[0-9][0-9]_*.md; do
        [[ "$(basename "$f")" == "00_ROUTER.md" ]] && continue
        [[ -f "$f" ]] || continue
        cat "$f"
        echo ""
    done
}

cmd_validate() {
    local errors=0

    if ! command -v aux &>/dev/null; then
        echo "error: aux CLI not found. Install with: pip install aux-skills" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    # Check optional tree-sitter dependency
    if ! python -c "import tree_sitter" 2>/dev/null; then
        echo "warn: tree-sitter not installed (AST abstractness detection unavailable; regex fallback will run). Install with: pip install 'aux-skills[query]'" >&2
    fi

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux robert --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux robert --plan "$plan"
    else
        # CLI argument passthrough
        aux robert "$@"
    fi
}

case "${1:-help}" in
    help)
        cmd_help
        ;;
    init)
        cmd_init
        ;;
    validate)
        cmd_validate
        ;;
    schema)
        cmd_schema
        ;;
    run)
        shift
        cmd_run "$@"
        ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'skill.sh help' for usage" >&2
        exit 1
        ;;
esac
