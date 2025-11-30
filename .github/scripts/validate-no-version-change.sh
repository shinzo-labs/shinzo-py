#!/bin/bash

set -e

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
  echo "Please use 'npx changeset' to manage version bumps instead of manually editing pyproject.toml"
  exit 1
fi

echo "✅ Version validation passed: $current_version"
