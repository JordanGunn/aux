#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILLS=("grep" "find" "diff" "ls")

echo "aux: bootstrapping all skills..."
echo

failed=0

for skill in "${SKILLS[@]}"; do
    bootstrap_script="$ROOT_DIR/$skill/bootstrap.sh"
    if [[ -f "$bootstrap_script" ]]; then
        echo "--- $skill ---"
        if bash "$bootstrap_script"; then
            echo
        else
            echo "error: $skill bootstrap failed" >&2
            failed=$((failed + 1))
            echo
        fi
    else
        echo "warning: $skill/bootstrap.sh not found, skipping" >&2
        echo
    fi
done

if [[ $failed -gt 0 ]]; then
    echo "aux: $failed skill(s) failed to bootstrap"
    exit 1
fi

echo "aux: all skills bootstrapped successfully"
