#!/usr/bin/env bash
# Builds SCHEMA.json from skill and module metadata.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
SKILLS_DIR="$REPO_ROOT/skills"
HOUSEKEEPING_PATH="$REPO_ROOT/assets/HOUSEKEEPING.md"
OUTPUT_PATH="$REPO_ROOT/assets/SCHEMA.json"

if ! command -v jq > /dev/null 2>&1; then
  echo "sync-schema: jq is missing" >&2
  exit 1
fi

if [[ ! -f "$HOUSEKEEPING_PATH" ]]; then
  echo "sync-schema: ${HOUSEKEEPING_PATH#"$REPO_ROOT"/} is missing" >&2
  exit 1
fi

relative_path() {
  local path="$1"
  printf '%s\n' "${path#"$REPO_ROOT"/}"
}

parse_scalar() {
  local value="$1"

  if [[ "$value" == \"*\" ]]; then
    jq --exit-status --raw-output 'if type == "string" then . else error("not a string") end' <<< "$value"
    return
  fi

  if [[ "$value" == \'*\' ]]; then
    value="${value:1:${#value}-2}"
    printf '%s\n' "${value//\'\'/\'}"
    return
  fi

  printf '%s\n' "$value"
}

read_frontmatter_field() {
  local document_path="$1"
  local field="$2"
  local raw_value

  if ! raw_value="$({
    awk -v field="$field" '
      NR == 1 && $0 == "---" { in_frontmatter = 1; next }
      in_frontmatter && $0 == "---" { exit }
      in_frontmatter {
        line = $0
        sub(/^[[:space:]]*/, "", line)
        if (index(line, field ":") == 1) {
          sub(/^[^:]*:[[:space:]]*/, "", line)
          print line
          found = 1
          exit
        }
      }
      END { if (!found) exit 1 }
    ' "$document_path"
  })"; then
    echo "sync-schema: missing $field in $(relative_path "$document_path")" >&2
    exit 1
  fi

  if [[ -z "$raw_value" ]]; then
    echo "sync-schema: empty $field in $(relative_path "$document_path")" >&2
    exit 1
  fi

  parse_scalar "$raw_value"
}

collect_assets() {
  local directory
  local path

  {
    for directory in "$@"; do
      if [[ -d "$directory" ]]; then
        find "$directory" -type f -print
      fi
    done
  } | LC_ALL=C sort | while IFS= read -r path; do
    jq --null-input \
      --arg name "${path##*/}" \
      --arg path "$(relative_path "$path")" \
      '{name: $name, path: $path}'
  done | jq --slurp '.'
}

build_module() {
  local module_path="$1"
  local module_dir
  local name
  local description
  local assets

  module_dir="$(dirname "$module_path")"
  name="$(read_frontmatter_field "$module_path" name)"
  description="$(read_frontmatter_field "$module_path" description)"
  assets="$(collect_assets "$module_dir/assets" "$module_dir/scripts")"

  jq --null-input \
    --arg name "$name" \
    --arg description "$description" \
    --arg module "$(relative_path "$module_path")" \
    --argjson assets "$assets" \
    '{name: $name, description: $description, module: $module, assets: $assets}'
}

build_skill() {
  local skill_path="$1"
  local skill_dir
  local module_path
  local name
  local description
  local modules
  local assets

  skill_dir="$(dirname "$skill_path")"
  name="$(read_frontmatter_field "$skill_path" name)"
  description="$(read_frontmatter_field "$skill_path" description)"
  modules="$({
    if [[ -d "$skill_dir/modules" ]]; then
      find "$skill_dir/modules" -mindepth 2 -maxdepth 2 -name MODULE.md -type f -print |
        LC_ALL=C sort | while IFS= read -r module_path; do
          build_module "$module_path"
        done
    fi
  } | jq --slurp '.')"
  assets="$(collect_assets "$skill_dir/assets" "$skill_dir/scripts")"

  jq --null-input \
    --arg name "$name" \
    --arg description "$description" \
    --arg skill "$(relative_path "$skill_path")" \
    --argjson modules "$modules" \
    --argjson assets "$assets" \
    '{name: $name, description: $description, skill: $skill, modules: $modules, assets: $assets}'
}

skill_count=0
skills="$({
  while IFS= read -r skill_path; do
    build_skill "$skill_path"
  done < <(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -name SKILL.md -type f -print | LC_ALL=C sort)
} | jq --slurp '.')"
skill_count="$(jq 'length' <<< "$skills")"

output_tmp="$(mktemp "$REPO_ROOT/.SCHEMA.json.XXXXXX")"
trap 'rm -f "$output_tmp"' EXIT

jq --null-input \
  --arg housekeeping "$(relative_path "$HOUSEKEEPING_PATH")" \
  --argjson skills "$skills" \
  '{housekeeping: $housekeeping, skills: $skills}' > "$output_tmp"

mv "$output_tmp" "$OUTPUT_PATH"
trap - EXIT

echo "sync-schema: wrote $(relative_path "$OUTPUT_PATH") with $skill_count skills"
