#!/usr/bin/env bash
# Syncs HOUSEKEEPING.md and formats the repository. With --check, reports problems instead of fixing them.
set -euo pipefail

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

"$SCRIPT_DIR/sync-housekeeping.sh" "$@"
"$SCRIPT_DIR/format.sh" "$@"
