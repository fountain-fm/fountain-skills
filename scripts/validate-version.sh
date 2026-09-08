#!/usr/bin/env bash
# Checks that the package.json version is greater than the version on the base branch.
# Usage: validate-version.sh [base-ref]
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
BASE_REF="${1:-origin/main}"

if ! command -v jq > /dev/null 2>&1; then
  echo "validate-version: jq is missing" >&2
  exit 1
fi

version="$(jq --raw-output '.version' "$REPO_ROOT/package.json")"
base_version="$(git -C "$REPO_ROOT" show "$BASE_REF:package.json" | jq --raw-output '.version')"

# sort -V puts the greater semver last, so the new version must both differ from the base and sort after it.
greater_version="$(printf '%s\n%s\n' "$base_version" "$version" | sort -V | tail -1)"
if [[ "$version" == "$base_version" || "$greater_version" != "$version" ]]; then
  echo "validate-version: version $version must be greater than $base_version on $BASE_REF" >&2
  echo "validate-version: run scripts/bump-version.sh" >&2
  exit 1
fi

echo "validate-version: $version is greater than $base_version on $BASE_REF"
