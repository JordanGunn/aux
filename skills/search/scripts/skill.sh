#!/usr/bin/env bash
# search skill - Hierarchical fd → rg [→ tree-sitter] pipeline
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
search - Hierarchical file-discovery + content-search [+ AST-structure] pipeline

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a search (plan mode only)

Usage (run):
  skill.sh run --stdin                           # Read plan JSON from stdin (required)

Note: search requires a full composite plan (surface + search sub-plans).
      Add a "structure" field for optional tier-3 tree-sitter AST matching.
      Use --schema to see the plan structure.

Examples:
  # Two-tier (fd → rg)
  echo '{"root":"/path","surface":{"root":"/path","globs":["*.py"]},"search":{"root":"/path","patterns":[{"value":"TODO"}]}}' \
    | skill.sh run --stdin

  # Three-tier (fd → rg → tree-sitter)
  echo '{"root":"/path","surface":{"root":"/path","globs":["*.py"]},"search":{"root":"/path","patterns":[{"value":"def "}]},"structure":{"query":"(function_definition name: (identifier) @fn)","language":"python"}}' \
    | skill.sh run --stdin

Schema:
  skill.sh schema

Execution backend: aux search (aux-skills CLI)
EOF
}

cmd_init() {
    local refs_dir="$SKILL_DIR/references"
    local idx=1

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

    for f in "$refs_dir"/[0-9][0-9]_*.md; do
        [[ "$(basename "$f")" == "00_ROUTER.md" ]] && continue
        [[ -f "$f" ]] || continue
        cat "$f"
        echo ""
    done
}

cmd_validate() {
    if ! command -v aux &>/dev/null; then
        echo "error: aux CLI not found. Install with: pip install aux-skills" >&2
        return 1
    fi
    aux doctor
}

cmd_schema() {
    aux search --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        local plan
        plan=$(cat)
        aux search --plan "$plan"
    else
        echo "error: search requires --stdin (plan mode only)" >&2
        echo "run 'skill.sh help' for usage" >&2
        exit 1
    fi
}

case "${1:-help}" in
    help)    cmd_help ;;
    init)    cmd_init ;;
    validate) cmd_validate ;;
    schema)  cmd_schema ;;
    run)     shift; cmd_run "$@" ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'skill.sh help' for usage" >&2
        exit 1
        ;;
esac
