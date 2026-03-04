#!/usr/bin/env bash
# rename skill - Move/rename files and directories
# Invokes the aux CLI as the execution backend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

cmd_help() {
    cat <<'EOF'
rename - Move/rename files and directories

Commands:
  help                   Show this help message
  init                   Emit all skill reference docs (concatenated)
  validate               Verify the skill is runnable
  schema                 Emit JSON schema for plan input
  run [opts]             Execute a rename (dry-run by default)

Usage (run):
  skill.sh run --stdin [--apply]             # Read plan JSON from stdin
  skill.sh run <src> <dst> [options]         # Simple mode

Two-phase execution:
  Phase 1: skill.sh run --stdin              → dry-run preview, no writes
  Phase 2: skill.sh run --stdin --apply      → apply moves

Options (simple mode):
  <src>                  Source path
  <dst>                  Destination path
  --backup               Copy src to .bak before moving
  --overwrite            Allow overwriting existing destination
  --apply                Apply changes to disk

Examples:
  # Dry run via stdin
  echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
    | skill.sh run --stdin

  # Apply
  echo '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' \
    | skill.sh run --stdin --apply

  # Simple mode
  skill.sh run /path/old.py /path/new.py

Execution backend: aux rename (aux-skills CLI)
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
    aux rename --schema
}

cmd_run() {
    local apply_flag=""
    local remaining_args=()

    for arg in "$@"; do
        if [[ "$arg" == "--apply" ]]; then
            apply_flag="--apply"
        else
            remaining_args+=("$arg")
        fi
    done

    if [[ "${remaining_args[0]:-}" == "--stdin" ]]; then
        local plan
        plan=$(cat)
        aux rename --plan "$plan" $apply_flag
    else
        aux rename "${remaining_args[@]}" $apply_flag
    fi
}

case "${1:-help}" in
    help)     cmd_help ;;
    init)     cmd_init ;;
    validate) cmd_validate ;;
    schema)   cmd_schema ;;
    run)      shift; cmd_run "$@" ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'skill.sh help' for usage" >&2
        exit 1
        ;;
esac
