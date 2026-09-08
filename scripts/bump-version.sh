#!/usr/bin/env bash
# Raises the package.json minor version one time for each branch, and does nothing when the branch
# already carries a raise.
# Usage: bump-version.sh [base-ref]
set -euo pipefail

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
BASE_REF="${1:-}"

if [[ -z "$BASE_REF" ]]; then
  # Prefer the remote branch, because a local main goes stale on a machine that only fetches.
  if git -C "$REPO_ROOT" rev-parse --verify --quiet origin/main > /dev/null; then
    BASE_REF="origin/main"
  else
    BASE_REF="main"
  fi
fi

if "$SCRIPT_DIR/validate-version.sh" "$BASE_REF" > /dev/null 2>&1; then
  exit 0
fi

base_version="$(git -C "$REPO_ROOT" show "$BASE_REF:package.json" | jq --raw-output '.version')"
next_version="$(awk -F. '{print $1 "." $2 + 1 ".0"}' <<< "$base_version")"

jq --arg version "$next_version" '.version = $version' "$REPO_ROOT/package.json" > "$REPO_ROOT/package.json.tmp"
mv "$REPO_ROOT/package.json.tmp" "$REPO_ROOT/package.json"
echo "bump-version: raised the version to $next_version"
