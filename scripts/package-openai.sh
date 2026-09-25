#!/usr/bin/env bash
# Zips the committed plugin for the OpenAI plugin submission portal into dist/.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
# The portal can derive the Codex manifest from a root plugin.json, so only the Codex manifest ships.
PLUGIN_PATHS=(.codex-plugin skills LICENSE README.md)

cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain -- "${PLUGIN_PATHS[@]}")" ]]; then
  echo "package-openai: uncommitted changes are left out of the zip" >&2
fi

version="$(jq --raw-output '.version' .codex-plugin/plugin.json)"
archive_path="dist/fountain-openai-$version.zip"

mkdir -p dist
git archive --format=zip --output="$archive_path" HEAD "${PLUGIN_PATHS[@]}"
echo "package-openai: wrote $archive_path"
