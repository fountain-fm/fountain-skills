#!/usr/bin/env bash
# Copies the package.json version into every plugin manifest. With --check, reports drift instead of writing it.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
MANIFESTS=(plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json)

if ! command -v jq > /dev/null 2>&1; then
  echo "sync-version: jq is missing" >&2
  exit 1
fi

check_mode=false
if [[ "${1:-}" == "--check" ]]; then
  check_mode=true
fi

version="$(jq --raw-output '.version' "$REPO_ROOT/package.json")"

stale_count=0
for manifest in "${MANIFESTS[@]}"; do
  manifest_path="$REPO_ROOT/$manifest"

  if [[ "$(jq --raw-output '.version // ""' "$manifest_path")" == "$version" ]]; then
    continue
  fi

  if [[ "$check_mode" == true ]]; then
    echo "sync-version: stale $manifest" >&2
    stale_count=$((stale_count + 1))
  else
    jq --arg version "$version" '.version = $version' "$manifest_path" > "$manifest_path.tmp"
    mv "$manifest_path.tmp" "$manifest_path"
    echo "sync-version: updated $manifest to $version"
  fi
done

if [[ "$stale_count" -gt 0 ]]; then
  echo "sync-version: run 'npm run sync-version' to fix $stale_count file(s)" >&2
  exit 1
fi
