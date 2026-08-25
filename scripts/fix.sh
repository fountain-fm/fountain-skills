#!/usr/bin/env bash
# Syncs HOUSEKEEPING.md and formats the repository. With --check, reports problems instead of fixing them
# and validates the Claude plugin manifests.
set -euo pipefail

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

"$SCRIPT_DIR/sync-housekeeping.sh" "$@"
"$SCRIPT_DIR/format.sh" "$@"

if [[ "${1:-}" == "--check" ]]; then
  "$SCRIPT_DIR/validate-claude-plugin.sh"
fi
