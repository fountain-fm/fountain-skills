#!/usr/bin/env bash
# Formats Markdown, shell, and Python files. Formats the whole repository when no paths are given.
# Usage: format.sh [--check] [path ...]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF_VERSION="0.16.1"

check_mode=false
paths=()
for argument in "$@"; do
  if [[ "$argument" == "--check" ]]; then
    check_mode=true
  else
    paths+=("$argument")
  fi
done

# Split the given paths: ruff formats Python, prettier formats everything else it recognises.
python_paths=()
prettier_paths=()
if [[ ${#paths[@]} -gt 0 ]]; then
  for path in "${paths[@]}"; do
    [[ -e "$path" ]] || continue
    if [[ "$path" == *.py ]]; then
      python_paths+=("$path")
    else
      prettier_paths+=("$path")
    fi
  done
else
  prettier_paths=(".")
  if [[ -n "$(find "$REPO_ROOT" -name node_modules -prune -o -name '*.py' -print -quit)" ]]; then
    python_paths=(".")
  fi
fi

cd "$REPO_ROOT"

if [[ ${#prettier_paths[@]} -gt 0 ]]; then
  prettier_flags=(--ignore-unknown --log-level warn)
  if [[ "$check_mode" == true ]]; then
    prettier_flags+=(--check)
  else
    prettier_flags+=(--write)
  fi
  npx --no-install prettier "${prettier_flags[@]}" "${prettier_paths[@]}"
fi

if [[ ${#python_paths[@]} -gt 0 ]]; then
  if ! command -v uv > /dev/null 2>&1; then
    echo "format: uv is missing - run 'npm run setup'" >&2
    exit 1
  fi
  if [[ "$check_mode" == true ]]; then
    uvx "ruff@$RUFF_VERSION" format --check "${python_paths[@]}"
    uvx "ruff@$RUFF_VERSION" check "${python_paths[@]}"
  else
    uvx "ruff@$RUFF_VERSION" format "${python_paths[@]}"
    uvx "ruff@$RUFF_VERSION" check --fix "${python_paths[@]}"
  fi
fi
