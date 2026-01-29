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
ls - Deterministic directory state inspection (bounded inventory + ranking)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  run [opts]                   Execute a deterministic directory inventory

Options (run):
  --stdin                      Read plan JSON from stdin (ls_plan_v1)
EOF
}

cmd_validate() {
    local errors=0

    if ! command -v uv &>/dev/null; then
        echo "error: uv not found. Install from https://docs.astral.sh/uv/" >&2
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

    if [[ ! -f "$SRC_DIR/validate.py" ]]; then
        echo "error: missing $SRC_DIR/validate.py" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$ASSETS_DIR/ls_config_v1.json" ]]; then
        echo "error: missing $ASSETS_DIR/ls_config_v1.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/ls_config_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/ls_config_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/ls_plan_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/ls_plan_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -f "$SCHEMAS_DIR/ls_result_bundle_v1.schema.json" ]]; then
        echo "error: missing $SCHEMAS_DIR/ls_result_bundle_v1.schema.json" >&2
        errors=$((errors + 1))
    fi

    if [[ ! -d "$ROOT_DIR/.aux/ls" ]]; then
        echo "error: missing directory $ROOT_DIR/.aux/ls" >&2
        errors=$((errors + 1))
    elif [[ ! -w "$ROOT_DIR/.aux/ls" ]]; then
        echo "error: directory not writable: $ROOT_DIR/.aux/ls" >&2
        errors=$((errors + 1))
    fi

    if [[ $errors -gt 0 ]]; then
        return 1
    fi

    # Fail-closed asset/config validation.
    if ! uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/validate.py"; then
        return 1
    fi

    if ! uv run -q --no-progress --project "$SRC_DIR" python "$SRC_DIR/cli.py" validate; then
        return 1
    fi

    echo "ok: ls skill is runnable"
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
    run)
        shift
        cmd_run "$@"
        ;;
    *)
        echo "error: unknown command '$1'" >&2
        echo "run 'ls help' for usage" >&2
        exit 1
        ;;
 esac
