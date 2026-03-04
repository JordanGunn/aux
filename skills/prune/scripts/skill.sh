#!/usr/bin/env bash
# prune skill - Tiered dead code candidate audit
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
prune - Tiered dead code candidate audit (advisory — requires human verification)

ADVISORY: Output is static analysis only. Never act on prune results without
running `aux usages` to verify each candidate and reviewing the code.

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a prune audit

Usage (run):
  skill.sh run --root <path> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --scope <scope>              Analysis scope: 'symbols' or 'files' (repeatable; default: symbols)
  --language <name>            Tree-sitter language override (symbols scope)
  --min-name-length <n>        Skip symbols shorter than N chars (default: 4)
  --max-refs <n>               Flag candidates with <= N external refs (default: 0)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-symbols <n>            Cap on symbols analyzed

Examples:
  skill.sh run --root ./src --glob "**/*.py"
  skill.sh run --root ./src --glob "**/*.py" --scope files
  skill.sh run --root ./src --glob "**/*.py" --scope symbols --max-refs 1
  echo '{"root":"/path","globs":["**/*.py"],"scope":["symbols"]}' | skill.sh run --stdin

Execution backend: aux prune (aux-skills CLI)
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

    # Check optional tree-sitter dependency (required for symbols scope)
    if ! python -c "import tree_sitter" 2>/dev/null; then
        echo "warn: tree-sitter not installed (symbols scope unavailable). Install with: pip install 'aux-skills[query]'" >&2
        echo "warn: use --scope files for text-only analysis without tree-sitter" >&2
    fi

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux prune --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux prune --plan "$plan"
    else
        # CLI argument passthrough
        aux prune "$@"
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
