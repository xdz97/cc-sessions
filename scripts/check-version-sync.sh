#!/usr/bin/env bash
#
# Version Sync Validation Script for cc-sessions
#
# Checks that package.json and pyproject.toml have matching version numbers.
# Exit code 0 if versions match, exit code 1 if mismatched.
#
# Usage:
#   ./scripts/check-version-sync.sh
#   scripts/check-version-sync.sh (from project root)
#

set -euo pipefail

# Get repo root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

# File paths
PACKAGE_JSON="$REPO_ROOT/package.json"
PYPROJECT_TOML="$REPO_ROOT/pyproject.toml"

# Check files exist
if [ ! -f "$PACKAGE_JSON" ]; then
    echo "❌ Error: package.json not found at $PACKAGE_JSON"
    exit 1
fi

if [ ! -f "$PYPROJECT_TOML" ]; then
    echo "❌ Error: pyproject.toml not found at $PYPROJECT_TOML"
    exit 1
fi

# Extract version from package.json
NPM_VERSION=$(grep -m 1 '"version":' "$PACKAGE_JSON" | sed 's/.*"version": "\(.*\)".*/\1/')

# Extract version from pyproject.toml
PYTHON_VERSION=$(grep -m 1 'version =' "$PYPROJECT_TOML" | sed 's/.*version = "\(.*\)".*/\1/')

# Check if extraction succeeded
if [ -z "$NPM_VERSION" ]; then
    echo "❌ Error: Could not extract version from package.json"
    exit 1
fi

if [ -z "$PYTHON_VERSION" ]; then
    echo "❌ Error: Could not extract version from pyproject.toml"
    exit 1
fi

# Compare versions
if [ "$NPM_VERSION" = "$PYTHON_VERSION" ]; then
    echo "✓ Version sync OK: $NPM_VERSION"
    echo "  package.json: $NPM_VERSION"
    echo "  pyproject.toml: $PYTHON_VERSION"
    exit 0
else
    echo "❌ Version mismatch detected"
    echo "  package.json: $NPM_VERSION"
    echo "  pyproject.toml: $PYTHON_VERSION"
    echo ""
    echo "Fix: Update both files to have the same version number"
    exit 1
fi
