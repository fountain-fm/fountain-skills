#!/usr/bin/env bash
# Package the committed plugin for an OpenAI plugin update.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
# The update must use the name assigned to the approved OpenAI plugin.
OPENAI_PLUGIN_NAME="app-6aa429bc4d1c819198ad6571766be52b"

cd "$REPO_ROOT"

package_paths=(.codex-plugin/plugin.json assets/icon.png skills LICENSE)
source_ref="$(git rev-parse HEAD)"

if [[ -n "$(git status --porcelain -- "${package_paths[@]}")" ]]; then
  echo "package-openai: uncommitted changes are left out of the zip" >&2
fi

version="$(git show "$source_ref:.codex-plugin/plugin.json" | jq --exit-status --raw-output '.version')"
archive_path="$REPO_ROOT/dist/fountain-openai-$version.zip"
staging_dir="$(mktemp -d)"
trap 'rm -rf "$staging_dir"' EXIT

git archive --format=tar "$source_ref" "${package_paths[@]}" | tar -xf - -C "$staging_dir"

# The upload format uses a separate MCP configuration file.
manifest_path="$staging_dir/.codex-plugin/plugin.json"
jq '{mcpServers: .mcpServers}' "$manifest_path" > "$staging_dir/.mcp.json"
jq --arg plugin_name "$OPENAI_PLUGIN_NAME" \
  '.name = $plugin_name | .mcpServers = "./.mcp.json"' "$manifest_path" > "$staging_dir/plugin.json"
mv "$staging_dir/plugin.json" "$manifest_path"

(
  cd "$staging_dir"
  zip -q -r "$staging_dir/plugin.zip" .codex-plugin assets/icon.png .mcp.json skills LICENSE
)

mkdir -p dist
mv "$staging_dir/plugin.zip" "$archive_path"
echo "package-openai: wrote $archive_path"
