#!/usr/bin/env bash
# hotspots skill - Churn-weighted complexity hotspots per file (Tornhill-style)
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
hotspots - Churn-weighted complexity hotspots per file (Tornhill 2015)

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute hotspot analysis

Usage (run):
  skill.sh run --root <path> [options]
  skill.sh run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Repository root (required; may be subdir of repo)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --since <spec>               Git log window start (default: "14 days ago")
                               Git-style: "30 days ago", "2025-01-01", "all"
  --until <spec>               Git log window end (default: now)
  --min-commits <n>            Minimum commit count to include a file (default: 2)
  --max-results <n>            Cap on ranked file list (post-sort)
  --percentile <p>             Quadrant cutoff percentile (default: 0.75)

Examples:
  skill.sh run --root ./
  skill.sh run --root ./ --since "30 days ago"
  skill.sh run --root ./ --since all --min-commits 5
  skill.sh run --root ./ --max-results 20
  echo '{"root":"./","since":"all"}' | skill.sh run --stdin

Execution backend: aux hotspots (aux-skills CLI)
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

    if ! command -v git &>/dev/null; then
        echo "error: git not found. Install git and ensure it is in PATH" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    # Delegate to CLI doctor for full dependency check
    aux doctor
}

cmd_schema() {
    aux hotspots --schema
}

cmd_run() {
    if [[ "${1:-}" == "--stdin" ]]; then
        # Plan-based invocation: read JSON from stdin
        local plan
        plan=$(cat)
        aux hotspots --plan "$plan"
    else
        # CLI argument passthrough
        aux hotspots "$@"
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
