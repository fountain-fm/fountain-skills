#!/usr/bin/env bash
# Copies assets/HOUSEKEEPING.md into every skill. With --check, reports stale copies instead of writing them.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
SOURCE_FILE="$REPO_ROOT/assets/HOUSEKEEPING.md"

check_mode=false
if [[ "${1:-}" == "--check" ]]; then
  check_mode=true
fi

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "sync-housekeeping: $SOURCE_FILE is missing" >&2
  exit 1
fi

stale_count=0
for skill_dir in "$REPO_ROOT"/skills/*/; do
  [[ -d "$skill_dir" ]] || continue
  target_file="${skill_dir%/}/HOUSEKEEPING.md"

  if cmp --silent "$SOURCE_FILE" "$target_file" 2> /dev/null; then
    continue
  fi

  if [[ "$check_mode" == true ]]; then
    echo "sync-housekeeping: stale ${target_file#"$REPO_ROOT"/}" >&2
    stale_count=$((stale_count + 1))
  else
    cp "$SOURCE_FILE" "$target_file"
    echo "sync-housekeeping: updated ${target_file#"$REPO_ROOT"/}"
  fi
done

if [[ "$stale_count" -gt 0 ]]; then
  echo "sync-housekeeping: run 'npm run housekeeping' to fix $stale_count file(s)" >&2
  exit 1
fi
