# Release Process

This repository uses [Changesets](https://github.com/changesets/changesets) to manage releases and versioning.

## Overview

The release workflow is fully automated via GitHub Actions:

1. **PR Creation**: Add a changeset to your PR
2. **PR Merge**: A Release PR is automatically created/updated
3. **Release PR Merge**: Package is published to PyPI and a GitHub release is created

## Adding a Changeset

When making changes that should trigger a release, add a changeset to your PR:

```bash
# Install dependencies (first time only)
pnpm install

# Create a changeset
pnpm changeset
```

This will prompt you to:
1. Select the type of change:
   - **Major** (1.0.0 → 2.0.0): Breaking changes
   - **Minor** (1.0.0 → 1.1.0): New features, backwards compatible
   - **Patch** (1.0.0 → 1.0.1): Bug fixes, backwards compatible
2. Write a summary of the changes

The changeset will be saved as a markdown file in `.changeset/` and should be committed with your PR.

## Workflow Details

### On Pull Request

When you open a PR to `main`, the following checks run:

- **Changeset validation**: Ensures a changeset is present (using `pnpm changeset status`)
- **Version validation**: Ensures `pyproject.toml` version hasn't been manually changed
- **Tests**: Runs tests across Python 3.10, 3.11, and 3.12
- **Linting**: Runs Black, Ruff, and MyPy

### On Merge to Main

When your PR is merged to `main`:

1. **If changesets exist and version unchanged**:
   - A Release PR is created/updated with title "Release vX.X.X"
   - The changeset determines the new version based on all pending changesets
   - `pyproject.toml` is automatically updated with the new version
   - Changesets are consumed and their contents added to CHANGELOG.md (if present)

2. **If version has changed (Release PR merged)**:
   - Package is built using Python's `build` module
   - Published to PyPI using the `PYPI_API_TOKEN` secret
   - GitHub release is created with tag `vX.X.X`
   - Release notes are extracted from the Release PR body

## Release PR

The Release PR will:
- Have the branch name `changeset-release/main`
- Update `pyproject.toml` with the new version
- Consume all changesets and add them to the changelog
- Show all changes that will be included in the release

**Do not manually edit the Release PR** - it's managed by the changesets action.

## Manual Version Bumps (Not Recommended)

If you need to manually bump the version without changesets:

1. Update `version` in `pyproject.toml`
2. Update `version` in `package.json` (keep them in sync)
3. Commit and push to `main`

The workflow will detect the version change and automatically publish.

However, **this bypasses the changelog generation** and is not recommended. Always prefer using changesets.

## Troubleshooting

### "No changesets found" error on PR

Make sure you've:
1. Run `pnpm changeset` and committed the generated `.changeset/*.md` file
2. The changeset file is not named `README.md` or `config.json`

### Version validation fails

This means you manually changed the version in `pyproject.toml`. Either:
1. Revert the version change and use a changeset instead, or
2. Update both `pyproject.toml` and `package.json` if this is intentional

### Release PR not created

Check that:
1. Your PR included a changeset file
2. The changeset file was committed in the `.changeset/` directory
3. The base branch is `main`

### PyPI publish fails

Check that:
1. `PYPI_API_TOKEN` secret is configured correctly
2. The version doesn't already exist on PyPI (versions cannot be overwritten)
3. The package builds successfully (`python -m build`)

## Example Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/add-cool-feature

# 2. Make your changes
# ... edit files ...

# 3. Install dependencies (first time)
pnpm install

# 4. Create a changeset
pnpm changeset
# Select "minor" for a new feature
# Write: "Add cool new feature for doing X"

# 5. Commit everything
git add .
git commit -m "Add cool new feature"

# 6. Push and create PR
git push origin feature/add-cool-feature

# 7. After PR is approved and merged:
#    - Release PR is automatically created
#    - Review the Release PR
#    - Merge the Release PR to publish

# 8. Package is now live on PyPI! 🎉
```
