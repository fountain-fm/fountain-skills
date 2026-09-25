#!/usr/bin/env bash
# Zips the committed skills for the Skills step of the OpenAI plugin submission portal into dist/.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain -- skills)" ]]; then
  echo "package-openai: uncommitted changes are left out of the zip" >&2
fi

version="$(jq --raw-output '.version' package.json)"
archive_path="dist/fountain-openai-$version.zip"

mkdir -p dist
rm -f "$archive_path"
git archive --format=zip --output="$archive_path" HEAD skills
echo "package-openai: wrote $archive_path"
