#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$SKILL_DIR/../.." && pwd)"

ASSETS_DIR="$SKILL_DIR/assets"
SCHEMAS_DIR="$ASSETS_DIR/schemas"

cmd_help() {
    cat <<'EOF'
diff - Deterministic git diff inspection (bounded summary + optional patch)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  discover [opts]              Run discovery phase (enumerate change candidates)
  run [opts]                   Execute a bounded diff

Options (discover/run):
  --stdin                      Read plan JSON from stdin
EOF
}

cmd_validate() {
    local errors=0

    if ! command -v uv &>/dev/null; then
        echo "error: uv not found. Install from https://docs.astral.sh/uv/" >&2
        errors=$((errors + 1))
    fi

    if ! command -v git &>/dev/null; then
        echo "error: git not found" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SRC_DIR/pyproject.toml" ]]; then
        echo "error: missing $SRC_DIR/pyproject.toml" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SRC_DIR/cli.py" ]]; then
        echo "error: missing $SRC_DIR/cli.py" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/diff_plan_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/diff_plan_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/diff_summary_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/diff_summary_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/diff_receipt_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/diff_receipt_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    if ! uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/cli.py" validate; then
        return 1
    fi

    echo "ok: diff skill is runnable"
}

cmd_discover() {
    uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/cli.py" discover "$@"
}

cmd_run() {
    uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/cli.py" run "$@"
}

case "${1:-help}" in
    help)
        cmd_help
        ;;
    validate)
        cmd_validate
        ;;
    discover)
        shift
        cmd_discover "$@"
        ;;
    run)
        shift
        cmd_run "$@"
        ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'diff help' for usage" >&2
        exit 1
        ;;
esac
