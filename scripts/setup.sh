#!/usr/bin/env bash
# Installs the formatting tools and enables the git hooks. Run this once after you clone the repository.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v npm > /dev/null 2>&1; then
  echo "setup: npm is missing - install Node.js from https://nodejs.org" >&2
  exit 1
fi

npm install

# uv runs ruff, the Python formatter. Ruff is not on npm, so it needs its own installer.
if ! command -v uv > /dev/null 2>&1; then
  if command -v brew > /dev/null 2>&1; then
    brew install uv
  else
    echo "setup: uv is missing - install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi
fi

git config core.hooksPath .githooks

echo "setup: done"
