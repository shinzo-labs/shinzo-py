# Changesets

This directory contains changesets for managing releases of the shinzo-py Python SDK.

## How to add a changeset

When making changes that should trigger a release, run:

```bash
npx changeset
```

This will guide you through creating a changeset file that describes:
- Which type of change this is (major, minor, or patch)
- A summary of the changes

The changeset will be consumed when a release PR is created and merged.

## Release process

1. **Create a PR** with your changes and a changeset
2. **When merged to main**, a Release PR will be automatically created/updated
3. **Merge the Release PR** to publish to PyPI and create a GitHub release
