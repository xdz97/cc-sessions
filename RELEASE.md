# Release Workflow for cc-sessions

This document describes the complete release process for the cc-sessions package, which publishes to both PyPI (Python) and npm (JavaScript).

## Overview

The release workflow follows a simplified `next` → `main` pattern where:
- **Development work** happens on feature branches that merge into the long-lived `next` branch
- **Release preparation** happens continuously on `next` as changes accumulate
- **Publishing** happens from `main` after merging from `next` and creating tags

## Pre-Release Preparation

Before running the release scripts, you must manually prepare the release on the `next` branch.

### 1. Decide on Version Number

Follow semantic versioning (0.MAJOR.MINOR):
- **MAJOR bump** (0.2.x → 0.3.0): Significant new features, architectural changes
- **MINOR bump** (0.2.7 → 0.2.8): Bug fixes, small features, patches

### 2. Update Version Numbers

Edit both files to have the same version:

**package.json** (line 3):
```json
"version": "0.3.0"
```

**pyproject.toml** (line 7):
```toml
version = "0.3.0"
```

### 3. Update CHANGELOG.md

Rename the "Unreleased" section to the new version with date:

```markdown
## [0.3.0] - 2025-10-09

### Added
- Feature descriptions here

### Changed
- Change descriptions here

### Fixed
- Bug fix descriptions here
```

### 4. Commit the Changes

```bash
git add package.json pyproject.toml CHANGELOG.md
git commit -m "Prepare release v0.3.0"
```

## Running Release Validation

Once preparation is complete, validate that everything is ready:

```bash
python scripts/prepare-release.py
```

### What It Checks

The validation script runs 7 checks:

1. **Version Sync**: package.json and pyproject.toml match
2. **On next Branch**: Currently on `next` (not `main` or feature branches)
3. **CHANGELOG Updated**: Has `## [X.Y.Z] - YYYY-MM-DD` section (not "Unreleased")
4. **Clean Git State**: No uncommitted changes
5. **Python Builds**: `python -m build` succeeds
6. **npm Validates**: `npm pack --dry-run` succeeds
7. **Required Tools Present**: python, npm, twine, git all installed

### Output Modes

**Interactive Mode** (default):
- Detailed format with actionable guidance for failures
- Offers to launch publish script on success

**Automated Mode** (`--auto` flag):
- Simple checklist format for CI/automated runs
- Just exits with success/failure code

### Example Output

```
[1/7] Version Sync........................ ✓ PASS
      package.json: 0.3.0
      pyproject.toml: 0.3.0

[3/7] Git State........................... ✗ FAIL
      Uncommitted files:
        - src/foo.py
      → Run: git add . && git commit -m "message"
```

## Publishing the Release

If all validation checks pass, you can proceed with publishing:

```bash
python scripts/publish-release.py
```

### What It Does

The publish script executes 15 steps atomically:

1. **Extract version** from package.json
2. **Run pre-flight checks**:
   - Re-run all prep script validations
   - Verify `main` is not ahead of `next`
   - Test PyPI credentials (twine)
   - Test npm credentials (npm whoami)
   - Test network connectivity
3. **POINT OF NO RETURN** - User confirmation required
4. **Merge** `next` → `main`
5. **Create git tag** `vX.Y.Z` on `main`
6. **Build Python artifacts** (`python -m build`)
7. **Publish to PyPI** (`twine upload dist/*`)
8. **Publish to npm** (`npm publish`)
9. **Push main branch** to GitHub
10. **Push tags** to GitHub
11. **Extract CHANGELOG section** for this version
12. **Create GitHub Release** with changelog notes
13. **Return to next branch**
14. **Create new "Unreleased" section** in CHANGELOG.md
15. **Commit** "Start next release cycle"

### Credentials Required

- **npm**: Uses `~/.npmrc` (must be logged in via `npm login`)
- **PyPI**: Uses `twine` authentication (keyring, env vars, or prompts)

### Error Handling

If publishing fails mid-process, you'll be prompted:

```
Publish failed at step X. Rollback local changes? (y/n)
```

**If yes**: Automatically delete tag, reset main, return to next

**If no**: Display manual recovery options:

```markdown
Option 1: Complete the release manually
  - Fix the issue that caused failure
  - Continue from step X in the sequence

Option 2: Rollback manually
  1. Delete tag: git tag -d vX.Y.Z
  2. Reset main: git checkout main && git reset --hard HEAD~1
  3. Return to next: git checkout next

Option 3: Partial rollback (if PyPI succeeded but npm failed)
  - Complete npm publish: npm publish
  - Then continue with remaining steps
```

## Version Consistency Utility

A standalone script for checking version sync:

```bash
scripts/check-version-sync.sh
```

Exits 0 if versions match, exits 1 if mismatched. Used by other scripts and can be called manually.

## Update Detection for Users

After publishing, users will be notified of available updates:

### Flag-Based Detection

The system caches update checks in `sessions-state.json` metadata:
- `update_available`: true/false/undefined
- `latest_version`: "0.3.0"
- `current_version`: "0.2.9"

### User Commands

Users can manage updates via the Sessions API:

```bash
sessions state update suppress    # Stop showing warnings
sessions state update check       # Force re-check on next session
sessions state update status      # Show current update status
```

### Auto-Update Feature

Users can enable automatic updates in `sessions-config.json`:

```json
{
  "features": {
    "auto_update": false  // Set to true to enable
  }
}
```

When enabled, the package automatically upgrades itself on session start when updates are detected.

## Post-Release Verification

After publishing, verify the release succeeded:

1. **Check PyPI**: https://pypi.org/project/cc-sessions/X.Y.Z/
2. **Check npm**: https://www.npmjs.com/package/cc-sessions/v/X.Y.Z
3. **Check GitHub**: https://github.com/GWUDCAP/cc-sessions/releases/tag/vX.Y.Z
4. **Test install**:
   ```bash
   # Python
   pip install --upgrade cc-sessions

   # JavaScript
   npm install -g cc-sessions@latest
   ```

## Troubleshooting

### "main is ahead of next"

This means commits exist on `main` that aren't on `next`. You must manually reconcile:

```bash
git checkout next
git merge main  # Bring main's changes into next
# Or if main should be reset:
git checkout main
git reset --hard next
```

### Build Failures

**Python build fails**:
- Check `pyproject.toml` syntax
- Ensure all package files exist
- Run `python -m build` manually to see full error

**npm validation fails**:
- Check `package.json` syntax
- Ensure files in `files` array exist
- Run `npm pack --dry-run` manually

### Credential Issues

**PyPI authentication fails**:
```bash
# Set up API token
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...

# Or use keyring
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__
```

**npm authentication fails**:
```bash
npm login  # Follow prompts
npm whoami # Verify logged in
```

### Version Mismatch

If package.json and pyproject.toml don't match:

```bash
# Check current values
./scripts/check-version-sync.sh

# Manually fix the mismatched file
# Then re-commit
```

## Quick Reference

**Full release from start to finish:**

```bash
# On next branch
vim package.json          # Set version
vim pyproject.toml        # Set version
vim CHANGELOG.md          # Rename "Unreleased" to "## [X.Y.Z] - YYYY-MM-DD"
git add package.json pyproject.toml CHANGELOG.md
git commit -m "Prepare release vX.Y.Z"

# Validate
python scripts/prepare-release.py

# Publish
python scripts/publish-release.py

# Verify
open https://pypi.org/project/cc-sessions/
open https://www.npmjs.com/package/cc-sessions
open https://github.com/GWUDCAP/cc-sessions/releases
```

**Emergency rollback** (if something goes wrong):

```bash
git tag -d vX.Y.Z                          # Delete local tag
git push origin :refs/tags/vX.Y.Z          # Delete remote tag
git checkout main
git reset --hard HEAD~1                     # Undo merge commit
git push -f origin main                     # Force push (be careful!)
git checkout next
```
