# Release Process

This repository uses [Commitizen](https://commitizen-tools.github.io/commitizen/) to manage releases and versioning.

## Overview

The release workflow is fully automated via GitHub Actions:

1. **PR Creation**: Use conventional commit messages in your PR
2. **PR Merge**: A Release PR is automatically created/updated based on commit messages
3. **Release PR Merge**: Package is published to PyPI and a GitHub release is created

## Conventional Commits

All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This enables automatic version bumping and changelog generation.

### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

- **feat**: A new feature (triggers MINOR version bump)
- **fix**: A bug fix (triggers PATCH version bump)
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without adding features or fixing bugs
- **test**: Adding or updating tests
- **chore**: Changes to build process or auxiliary tools

### Breaking Changes

To trigger a MAJOR version bump, add `BREAKING CHANGE:` in the commit footer or add `!` after the type:

```bash
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /v1/users endpoint has been removed. Use /v2/users instead.
```

### Examples

```bash
# Feature (minor bump)
feat(instrumentation): add support for custom exporters

# Bug fix (patch bump)
fix(config): correct validation for sampling rate

# Breaking change (major bump)
feat!: redesign configuration API

BREAKING CHANGE: Configuration now uses a class-based approach instead of dictionaries.
```

## Workflow Details

### On Pull Request

When you open a PR to `main`, the following checks run:

- **Conventional commits validation**: Ensures all commits follow conventional commits format
- **Version validation**: Ensures `pyproject.toml` version hasn't been manually changed
- **Tests**: Runs tests across Python 3.10, 3.11, and 3.12
- **Linting**: Runs Black, Ruff, and MyPy

### On Merge to Main

When your PR is merged to `main`:

1. **If commits since last tag and version unchanged**:
   - A Release PR is created/updated with title "Release vX.X.X"
   - Commitizen analyzes commit messages to determine version bump type
   - `pyproject.toml` is automatically updated with the new version
   - CHANGELOG.md is automatically generated from commit messages

2. **If version has changed (Release PR merged)**:
   - Package is built using Python's `build` module
   - Published to PyPI using the `PYPI_API_TOKEN` secret
   - GitHub release is created with tag `vX.X.X`
   - Release notes are extracted from CHANGELOG.md

## Release PR

The Release PR will:
- Have the branch name `release/automated`
- Update `pyproject.toml` with the new version
- Generate/update CHANGELOG.md with changes from commit messages
- Show all changes that will be included in the release

**Do not manually edit the Release PR** - it's managed by commitizen.

## Manual Version Bumps (Not Recommended)

If you need to manually bump the version:

1. Install commitizen: `pip install commitizen`
2. Run: `cz bump` (or `cz bump --dry-run` to preview)
3. Commit and push changes

However, **manual bumps should be rare** as the automated workflow handles most cases.

## Troubleshooting

### "Commit message does not follow conventional commits format" error on PR

Your commit messages must follow the conventional commits format. Fix by:
1. Use interactive rebase to reword commits: `git rebase -i origin/main`
2. Or squash and rewrite: `git reset --soft origin/main && git commit -m "feat: your feature description"`
3. Force push: `git push --force`

Alternatively, ask a maintainer to squash merge with a proper commit message.

### Version validation fails

This means you manually changed the version in `pyproject.toml`. Either:
1. Revert the version change and let commitizen handle it, or
2. Ensure the change is intentional (manual bump scenario)

### Release PR not created

Check that:
1. Your commits follow conventional commits format
2. Your commits include types that trigger version bumps (feat, fix, etc.)
3. The base branch is `main`
4. There are commits since the last tag

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

# 3. Commit with conventional commit format
git add .
git commit -m "feat(instrumentation): add support for custom exporters

Add ability to configure custom OTLP exporters with user-defined endpoints and authentication methods."

# 4. Push and create PR
git push origin feature/add-cool-feature

# 5. After PR is approved and merged:
#    - Release PR is automatically created based on commit messages
#    - Review the Release PR
#    - Merge the Release PR to publish

# 6. Package is now live on PyPI! 🎉
```

## Helper Tool

To make writing conventional commits easier, you can use commitizen interactively:

```bash
# Install in dev environment
pip install -e ".[dev]"

# Use interactive commit
cz commit

# Or just use cz as alias
cz c
```

This will prompt you through creating a properly formatted commit message.
