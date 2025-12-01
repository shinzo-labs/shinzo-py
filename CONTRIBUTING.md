# Contributing to the Shinzo Python SDK

## Overview

Contributions to this codebase are welcomed and appreciated. We encourage novice and professional developers alike to help improve the quality of our software, which is offered as a benefit to the developer community.

## Code of Conduct

As a member of our community, you are expected to follow all rules in our [Contributor Covenant Code of Conduct](./CODE_OF_CONDUCT.md). Please report unacceptable behavior through the channels specified in the covenant.

## Technical Contributions

### Issues

If you would like to raise any issues, please do so in the [Issues](https://github.com/shinzo-labs/shinzo-py/issues) section and a core contributor will respond in a timely manner. Issue threads may be closed if there are no additional comments added in a reasonable timeframe after the last update by a contributor on the thread.

### Pull Requests

If you would like to contribute code to the codebase, you may review the open issues in [Issues](https://github.com/shinzo-labs/shinzo-py/issues) to participate in discussion or ask to be assigned directly to it. If you would like to suggest a feature that is not already captured in the Issues section, please open a new Issue ticket.

Once you have been assigned an issue, the steps to contribute are:
1. Create a fork version of the repo.
2. Open a branch with a name prefixed with `feat/`, `fix/`, or `chore/` depending on the nature of the change. Use your best judgement when deciding on the prefix.
3. Implement the desired changes.
4. Add tests to any relevant test suites to validate functionality
5. Run all linting checks locally to ensure your code passes CI validation: `make lint-all` (this runs Black formatter check, Ruff linter, and MyPy type checker).
6. Commit your changes using `cz commit`. See the [Version Management](#version-management) section below for details on commit message format.
7. Open a Pull Request from your forked repo back to the main repo. Tag one of the core contributors as a reviewer.
8. Once the core contributor has reviewed the code and all comments have been resolved, the PR will be approved and merged into the `main` branch.
9. When your PR is merged, your conventional commit messages will be used to automatically create a release PR with proper version bumps and changelogs. Once the release PR is merged, updated packages will be published to PyPI automatically.

### Version Management

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) to manage versioning and publishing of the Python package.

#### Commit Helper

Use the `cz commit` command to create a commit message. This will guide you through creating a properly formatted commit message. All commit messages **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification, which the `cz commit` command will enforce. This format enables automatic semantic versioning and changelog generation.

```bash
# Install dev dependencies first
pip install -e ".[dev]"

# Use interactive commit
cz commit

# Or use the shorter alias
cz c
```

#### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- **feat**: A new feature (triggers MINOR version bump, e.g., 1.0.0 → 1.1.0)
- **fix**: A bug fix (triggers PATCH version bump, e.g., 1.0.0 → 1.0.1)
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without adding features or fixing bugs
- **test**: Adding or updating tests
- **chore**: Changes to build process or auxiliary tools

**Scopes (optional):** Helps categorize commits (e.g., `instrumentation`, `config`, `exporters`)

To trigger a MAJOR version bump (e.g., 1.0.0 → 2.0.0), add `!` after the type in your commit message.

```bash
feat!: redesign configuration API

BREAKING CHANGE: Configuration now uses a class-based approach instead of dictionaries.
```

This will guide you through creating a properly formatted commit message.

#### Version Bump Guidelines

Commitizen automatically determines the version bump based on commit types:
- **feat** commits → MINOR bump (1.0.0 → 1.1.0)
- **fix** commits → PATCH bump (1.0.0 → 1.0.1)
- **BREAKING CHANGE** or `!` → MAJOR bump (1.0.0 → 2.0.0)
- Other types → No version bump

#### Important: Never Manually Update Package Versions

- ❌ **Don't** manually edit the version field in `pyproject.toml`
- ✅ **Do** use conventional commit messages
- ✅ **Do** let commitizen and CI/CD handle versioning automatically

The CI system will automatically reject PRs that contain manual version changes to ensure consistency.

## Non-Technical Contributions

Shinzo can only grow with the support of a vibrant developer community and strong partnerships with other organizations and communities. If you think there may be an opportunity to collaborate or advance the project in some way, please reach out to the contact below.

## Contact

If you have any questions or comments about the guidelines here or anything else about the software, feel free to join the discussion on our [Discord server](https://discord.gg/UYUdSdp5N8) or contact the project maintainer Austin Born (austin@shinzolabs.com, [@austinbuilds](https://x.com/austinbuilds)) directly.
