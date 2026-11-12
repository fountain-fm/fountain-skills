#!/usr/bin/env bash
# Commits the files that the Claude directory accepts from an unverified organization to the claude-directory branch.
# Builds from origin/main, or from the ref after --source. With --push, also pushes the branch to origin.
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
TARGET_BRANCH="claude-directory"
INCLUDED_SKILL="fountain-onboarding"
INCLUDED_PATHS=(.mcp.json LICENSE "skills/$INCLUDED_SKILL")
# The directory listing shows this file as README.md, because the main README also lists skills it leaves out.
README_SOURCE_PATH="assets/directory-readme.md"
# Claude Code does not read these manifest fields, and the listing kept their values from the first submission.
LISTING_ONLY_FIELDS_FILTER='del(.icon, .documentationUrl, .supportUrl, .termsOfServiceUrl)'
# The directory finds the icon at this path with no icon field, which would refer to an image from code.
ICON_SOURCE_PATH="assets/icon.png"
ALLOWED_EXTENSIONS_PATTERN='\.(md|txt|json|ya?ml|png|jpe?g|gif|webp|ico)$'
ALLOWED_PLAIN_NAMES_PATTERN='^(LICENSE|\.gitignore)$'

cd "$REPO_ROOT"

push_mode=false
source_name="origin/main"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) push_mode=true ;;
    --source)
      source_name="$2"
      shift
      ;;
    *)
      echo "build-directory-branch: unknown argument $1" >&2
      exit 1
      ;;
  esac
  shift
done

git fetch --quiet origin
source_ref="$(git rev-parse --verify "$source_name^{commit}")"

# Build the tree in a temporary index, so that the working tree and the real index stay as they are.
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
index_file="$work_dir/index"
# Each sentence is on its own line, so dropping a line that names a left-out skill drops one sentence.
excluded_skills_pattern="$(git ls-tree --name-only "$source_ref" skills/ | sed 's|^skills/||' \
  | grep -v -x "$INCLUDED_SKILL" | paste -s -d '|' -)"
housekeeping_path="skills/$INCLUDED_SKILL/HOUSEKEEPING.md"
housekeeping_blob_id="$(git show "$source_ref:$housekeeping_path" \
  | { [[ -n "$excluded_skills_pattern" ]] && grep -v -E "$excluded_skills_pattern" || cat; } | git hash-object -w --stdin)"
manifest_blob_id="$(git show "$source_ref:.claude-plugin/plugin.json" | jq "$LISTING_ONLY_FIELDS_FILTER" \
  | git hash-object -w --stdin)"
{
  git ls-tree -r "$source_ref" -- "${INCLUDED_PATHS[@]}"
  printf '100644 blob %s\tREADME.md\n' "$(git rev-parse "$source_ref:$README_SOURCE_PATH")"
  printf '100644 blob %s\t.claude-plugin/plugin.json\n' "$manifest_blob_id"
  printf '100644 blob %s\t.claude-plugin/icon.png\n' "$(git rev-parse "$source_ref:$ICON_SOURCE_PATH")"
  printf '100644 blob %s\t%s\n' "$housekeeping_blob_id" "$housekeeping_path"
} | GIT_INDEX_FILE="$index_file" git update-index --add --index-info
tree_id="$(GIT_INDEX_FILE="$index_file" git write-tree)"

# Check each file against the directory policy for unverified organizations.
violation_count=0
while IFS= read -r file_path; do
  file_name="$(basename "$file_path")"
  if [[ ! "$file_name" =~ $ALLOWED_EXTENSIONS_PATTERN && ! "$file_name" =~ $ALLOWED_PLAIN_NAMES_PATTERN ]]; then
    echo "build-directory-branch: type not allowed: $file_path" >&2
    violation_count=$((violation_count + 1))
    continue
  fi
  [[ "$file_name" =~ \.(png|jpe?g|gif|webp|ico)$ ]] && continue
  file_content_path="$work_dir/content"
  git cat-file blob "$tree_id:$file_path" > "$file_content_path"
  if [[ "$(head -c 2 "$file_content_path")" == "#!" ]]; then
    echo "build-directory-branch: starts with #!: $file_path" >&2
    violation_count=$((violation_count + 1))
  elif [[ "$(LC_ALL=C tr -d '\000' < "$file_content_path" | wc -c)" -ne "$(wc -c < "$file_content_path")" ]] \
    || ! iconv -f UTF-8 -t UTF-8 "$file_content_path" > /dev/null 2>&1; then
    echo "build-directory-branch: not UTF-8 text: $file_path" >&2
    violation_count=$((violation_count + 1))
  elif [[ -n "$excluded_skills_pattern" ]] && grep -q -E "$excluded_skills_pattern" "$file_content_path"; then
    echo "build-directory-branch: names a skill that the branch leaves out: $file_path" >&2
    violation_count=$((violation_count + 1))
  fi
done < <(git ls-tree -r --name-only "$tree_id")

if [[ "$violation_count" -gt 0 ]]; then
  echo "build-directory-branch: $violation_count file(s) break the directory policy - nothing committed" >&2
  exit 1
fi

# Commit on top of the existing branch, and skip the commit when the content is unchanged.
parent_args=()
if parent_id="$(git rev-parse --verify --quiet "refs/remotes/origin/$TARGET_BRANCH")"; then
  if [[ "$(git rev-parse "$parent_id^{tree}")" == "$tree_id" ]]; then
    echo "build-directory-branch: origin/$TARGET_BRANCH already matches ${source_ref:0:7}"
    exit 0
  fi
  parent_args=(-p "$parent_id")
fi

version="$(git show "$source_ref:.claude-plugin/plugin.json" | jq --exit-status --raw-output '.version')"
commit_message="$version - Directory build of ${source_ref:0:7}"
commit_id="$(git commit-tree "$tree_id" ${parent_args[@]+"${parent_args[@]}"} -m "$commit_message")"
git update-ref "refs/heads/$TARGET_BRANCH" "$commit_id"
echo "build-directory-branch: $TARGET_BRANCH is now ${commit_id:0:7} ($commit_message)"

if [[ "$push_mode" == true ]]; then
  git push origin "$TARGET_BRANCH"
fi
