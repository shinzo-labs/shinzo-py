#!/bin/bash

set -e

# This script updates the version in pyproject.toml to match the version
# determined by changesets during the release PR process

if [ -z "$NEW_VERSION" ]; then
  echo "❌ Error: NEW_VERSION environment variable must be set"
  exit 1
fi

echo "Updating pyproject.toml version to $NEW_VERSION"

# Update version in pyproject.toml
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm -f pyproject.toml.bak

# Verify the change
current_version=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [ "$current_version" != "$NEW_VERSION" ]; then
  echo "❌ Error: Failed to update version. Expected $NEW_VERSION but got $current_version"
  exit 1
fi

echo "✅ Successfully updated version to $NEW_VERSION"
