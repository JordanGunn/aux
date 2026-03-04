#!/usr/bin/env bash
# find skill - Read-only tree-sitter structural search
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
find - Read-only tree-sitter structural search (AST-aware)

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] <query>           Execute a structural search

Usage (run):
  skill.sh run <query> --root <path> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  <query>                      Tree-sitter query string (positional, required)
  --root <path>                Root directory (required unless --file used)
  --file <path>                Explicit file to search (repeatable)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --language <name>            Language override (auto-detected if omitted)
  --max-matches <n>            Max total matches to return
  --languages                  List available/unavailable grammar packages

Examples:
  skill.sh run "(function_definition name: (identifier) @name)" --root ./src --glob "*.py"
  skill.sh run "(import_statement) @import" --root /path --glob "*.py" --max-matches 50
  echo '{"query":"(function_definition name: (identifier) @name)","root":"/path","globs":["*.py"]}' | skill.sh run --stdin

Grammar check:
  aux find --languages

Execution backend: aux find (aux-skills CLI)
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
        echo "warn: tree-sitter not installed (find unavailable). Install with: pip install 'aux-skills[query]'" >&2
    fi

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux find --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux find --plan "$plan"
    else
        # CLI argument passthrough
        aux find "$@"
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
