#!/usr/bin/env bash
# Validates the Claude plugin and marketplace manifests. Skips when the Claude Code CLI is missing.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

if ! command -v claude > /dev/null 2>&1; then
  echo "validate-claude-plugin: claude is missing - skipping"
  exit 0
fi

claude plugin validate "$REPO_ROOT"
