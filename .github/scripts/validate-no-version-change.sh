#!/bin/bash

set -e

# This script validates that the version in pyproject.toml has not been manually changed
# in feature branches. Version changes should only occur through commitizen via the
# automated release process on the changeset-release/main branch.

BASE_BRANCH=${GITHUB_BASE_REF:-main}
git fetch origin $BASE_BRANCH

# Extract version from pyproject.toml
get_version() {
  local file=$1
  grep -E '^version = ' "$file" | sed 's/version = "\(.*\)"/\1/'
}

current_version=$(get_version pyproject.toml)
base_version=$(git show origin/$BASE_BRANCH:pyproject.toml | grep -E '^version = ' | sed 's/version = "\(.*\)"/\1/')

# Check if version has changed from base branch
if [ "$current_version" != "$base_version" ]; then
  echo "❌ Error: Version should not change from base branch."
  echo "Base branch version: $base_version"
  echo "PR version: $current_version"
  echo ""
  echo "Version bumps are managed automatically by commitizen in the release process."
  echo "Do not manually edit the version in pyproject.toml."
  echo ""
  echo "Your changes will be included in the next release based on your commit messages."
  echo "Use conventional commit format: type(scope): subject"
  echo "Types: feat (minor bump), fix (patch bump), BREAKING CHANGE (major bump)"
  exit 1
fi

echo "✅ Version validation passed: $current_version"
