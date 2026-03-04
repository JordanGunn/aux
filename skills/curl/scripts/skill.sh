#!/usr/bin/env bash
# curl skill - Agent-optimised HTTP fetch with progressive disclosure
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
curl - Agent-optimised HTTP fetch with progressive disclosure

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (checks aux + httpx)
  schema                       Emit JSON schema for plan input
  run [opts] <url>             Fetch a URL and return clean extracted content

Usage (run):
  skill.sh run <url> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  <url>                        URL to fetch (positional)
  --method <GET|POST|...>      HTTP method (default: GET)
  --header <KEY:VALUE>         Request header (repeatable)
  --body <text>                Request body for POST/PUT/PATCH
  --mode <auto|text|markdown|json|raw>  Extraction mode (default: auto)
  --offset <n>                 Character offset for progressive disclosure (default: 0)
  --length <n>                 Characters to return from offset (default: 20000)
  --timeout <seconds>          Request timeout (default: 30.0)
  --no-follow-redirects        Do not follow HTTP redirects

Examples:
  skill.sh run https://docs.python.org/3/ --mode text
  skill.sh run https://api.example.com/data --mode json
  skill.sh run https://example.com --offset 20000        # next chunk
  echo '{"urls":["https://httpbin.org/json"],"mode":"json"}' | skill.sh run --stdin

Execution backend: aux curl (aux-skills CLI)
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

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux curl --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux curl --plan "$plan"
    else
        # CLI argument passthrough
        aux curl "$@"
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
