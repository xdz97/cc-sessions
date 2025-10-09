#!/usr/bin/env python3
"""
Release Preparation Script for cc-sessions

Validates that the repository is ready for release by checking:
1. Version sync between package.json and pyproject.toml
2. Currently on 'next' branch
3. CHANGELOG.md has dated version section (no "Unreleased")
4. Git working tree is clean
5. Python package builds successfully
6. npm package validates successfully
7. Required tools are present

Usage:
    python scripts/prepare-release.py           # Interactive mode (default)
    python scripts/prepare-release.py --auto    # Automated mode (CI-friendly)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional
import re


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ValidationCheck:
    """Represents a single validation check with results"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.message = ""
        self.details = []
        self.remedy = ""


def get_repo_root() -> Path:
    """Get the repository root directory"""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True,
        text=True,
        check=True
    )
    return Path(result.stdout.strip())


def read_json_version(file_path: Path) -> Optional[str]:
    """Read version from package.json"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('version')
    except Exception as e:
        return None


def read_toml_version(file_path: Path) -> Optional[str]:
    """Read version from pyproject.toml"""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip().startswith('version ='):
                    # Extract version string: version = "0.2.9"
                    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        return match.group(1)
        return None
    except Exception as e:
        return None


def check_version_sync(repo_root: Path) -> ValidationCheck:
    """Check that package.json and pyproject.toml versions match"""
    check = ValidationCheck("Version Sync", "package.json and pyproject.toml have matching versions")

    package_json = repo_root / 'package.json'
    pyproject_toml = repo_root / 'pyproject.toml'

    npm_version = read_json_version(package_json)
    python_version = read_toml_version(pyproject_toml)

    if npm_version is None:
        check.message = "Could not read version from package.json"
        check.remedy = f"Check that {package_json} exists and is valid JSON"
        return check

    if python_version is None:
        check.message = "Could not read version from pyproject.toml"
        check.remedy = f"Check that {pyproject_toml} exists and has 'version = \"X.Y.Z\"' line"
        return check

    if npm_version != python_version:
        check.message = f"Version mismatch"
        check.details = [
            f"package.json: {npm_version}",
            f"pyproject.toml: {python_version}"
        ]
        check.remedy = "Update both files to have the same version number"
        return check

    check.passed = True
    check.message = f"Versions synced: {npm_version}"
    check.details = [
        f"package.json: {npm_version}",
        f"pyproject.toml: {python_version}"
    ]
    return check


def check_on_next_branch() -> ValidationCheck:
    """Check that we're currently on the 'next' branch"""
    check = ValidationCheck("Branch Check", "Currently on 'next' branch")

    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()

        if current_branch != 'next':
            check.message = f"On branch '{current_branch}', not 'next'"
            check.remedy = "Run: git checkout next"
            return check

        check.passed = True
        check.message = "On 'next' branch"
        return check
    except subprocess.CalledProcessError as e:
        check.message = "Could not determine current branch"
        check.remedy = "Ensure you're in a git repository"
        return check


def check_changelog_updated(repo_root: Path) -> ValidationCheck:
    """Check that CHANGELOG.md has a dated version section (not 'Unreleased')"""
    check = ValidationCheck("CHANGELOG Updated", "Has dated version section matching package versions")

    changelog_path = repo_root / 'CHANGELOG.md'

    if not changelog_path.exists():
        check.message = "CHANGELOG.md not found"
        check.remedy = f"Create {changelog_path} with version history"
        return check

    # Get the current version
    package_json = repo_root / 'package.json'
    version = read_json_version(package_json)

    if not version:
        check.message = "Could not determine version to check against"
        check.remedy = "Fix version sync issue first"
        return check

    try:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Look for version section like: ## [0.3.0] - 2025-10-09
        version_pattern = rf'##\s*\[{re.escape(version)}\]\s*-\s*\d{{4}}-\d{{2}}-\d{{2}}'
        if not re.search(version_pattern, content):
            check.message = f"No dated section found for version {version}"
            check.details = [
                f"Expected format: ## [{version}] - YYYY-MM-DD",
                "Found 'Unreleased' section or missing version section"
            ]
            check.remedy = f"Update CHANGELOG.md: rename 'Unreleased' to '## [{version}] - YYYY-MM-DD'"
            return check

        check.passed = True
        check.message = f"Found version section for {version}"
        return check
    except Exception as e:
        check.message = f"Error reading CHANGELOG.md: {e}"
        return check


def check_git_clean() -> ValidationCheck:
    """Check that git working tree is clean"""
    check = ValidationCheck("Git State", "No uncommitted changes")

    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            files = [line.strip() for line in result.stdout.strip().split('\n')]
            check.message = f"{len(files)} uncommitted file(s)"
            check.details = files[:10]  # Show first 10 files
            if len(files) > 10:
                check.details.append(f"... and {len(files) - 10} more")
            check.remedy = "Run: git add . && git commit -m \"your message\""
            return check

        check.passed = True
        check.message = "Working tree clean"
        return check
    except subprocess.CalledProcessError as e:
        check.message = "Could not check git status"
        check.remedy = "Ensure you're in a git repository"
        return check


def check_python_build(repo_root: Path) -> ValidationCheck:
    """Check that Python package builds successfully"""
    check = ValidationCheck("Python Build", "python -m build succeeds")

    try:
        result = subprocess.run(
            ['python', '-m', 'build', '--outdir', 'dist-test'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Clean up test dist directory
        import shutil
        test_dist = repo_root / 'dist-test'
        if test_dist.exists():
            shutil.rmtree(test_dist)

        if result.returncode != 0:
            check.message = "Build failed"
            check.details = result.stderr.split('\n')[-5:]  # Last 5 lines of error
            check.remedy = "Fix build errors shown above"
            return check

        check.passed = True
        check.message = "Build successful"
        return check
    except FileNotFoundError:
        check.message = "python or build module not found"
        check.remedy = "Install: pip install build"
        return check
    except subprocess.TimeoutExpired:
        check.message = "Build timed out after 60 seconds"
        check.remedy = "Check for infinite loops or hanging processes"
        return check
    except Exception as e:
        check.message = f"Build error: {e}"
        return check


def check_npm_validate(repo_root: Path) -> ValidationCheck:
    """Check that npm package structure is valid"""
    check = ValidationCheck("npm Validation", "npm pack --dry-run succeeds")

    try:
        result = subprocess.run(
            ['npm', 'pack', '--dry-run'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            check.message = "npm pack validation failed"
            check.details = result.stderr.split('\n')[-5:]
            check.remedy = "Fix npm package issues shown above"
            return check

        check.passed = True
        check.message = "npm package valid"
        return check
    except FileNotFoundError:
        check.message = "npm not found"
        check.remedy = "Install Node.js and npm"
        return check
    except subprocess.TimeoutExpired:
        check.message = "npm pack timed out after 30 seconds"
        return check
    except Exception as e:
        check.message = f"npm validation error: {e}"
        return check


def check_required_tools() -> ValidationCheck:
    """Check that required tools are present"""
    check = ValidationCheck("Required Tools", "python, npm, twine, git all installed")

    tools = ['python', 'npm', 'twine', 'git']
    missing = []

    for tool in tools:
        try:
            subprocess.run(
                [tool, '--version'],
                capture_output=True,
                timeout=5
            )
        except FileNotFoundError:
            missing.append(tool)
        except Exception:
            missing.append(tool)

    if missing:
        check.message = f"{len(missing)} tool(s) missing"
        check.details = missing
        check.remedy = f"Install missing tools: {', '.join(missing)}"
        return check

    check.passed = True
    check.message = "All tools present"
    return check


def print_check_interactive(num: int, total: int, check: ValidationCheck):
    """Print check result in interactive mode with detailed formatting"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if check.passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"

    # Print header line
    dots = "." * (40 - len(check.name))
    print(f"[{num}/{total}] {check.name}{dots} {status}")

    # Print details
    if check.details:
        for detail in check.details:
            print(f"      {detail}")
    else:
        print(f"      {check.message}")

    # Print remedy if failed
    if not check.passed and check.remedy:
        print(f"      {Colors.YELLOW}→ {check.remedy}{Colors.RESET}")

    print()  # Blank line


def print_check_auto(check: ValidationCheck):
    """Print check result in auto mode with simple format"""
    status = "✓" if check.passed else "✗"
    print(f"{status} {check.name}: {check.message}")


def run_all_checks(repo_root: Path, interactive: bool) -> Tuple[list, int, int]:
    """Run all validation checks and return results"""
    checks = [
        check_version_sync(repo_root),
        check_on_next_branch(),
        check_changelog_updated(repo_root),
        check_git_clean(),
        check_python_build(repo_root),
        check_npm_validate(repo_root),
        check_required_tools()
    ]

    passed = sum(1 for c in checks if c.passed)
    failed = len(checks) - passed

    if interactive:
        print()
        for i, check in enumerate(checks, 1):
            print_check_interactive(i, len(checks), check)
    else:
        for check in checks:
            print_check_auto(check)

    return checks, passed, failed


def main():
    """Main entry point"""
    # Parse arguments
    interactive = '--auto' not in sys.argv

    try:
        repo_root = get_repo_root()
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    if interactive:
        print(f"{Colors.BOLD}Release Preparation Validation{Colors.RESET}")
        print(f"Repository: {repo_root}")
        print(f"Mode: Interactive")
        print()

    # Run all checks
    checks, passed, failed = run_all_checks(repo_root, interactive)

    # Print summary
    if interactive:
        print("=" * 60)
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}All checks passed! ✓{Colors.RESET}\n")
            print("Ready to proceed with release publishing.")
            print("This will:")
            print("  - Merge 'next' → 'main'")
            print("  - Create git tag")
            print("  - Build and publish to PyPI and npm")
            print("  - Push to GitHub and create release")
            print("  - Create new 'Unreleased' section in CHANGELOG")
            print()

            response = input("Run publish script now? (y/n): ").strip().lower()
            if response == 'y':
                print(f"\n{Colors.BLUE}Launching publish script...{Colors.RESET}")
                subprocess.run(['python', str(repo_root / 'scripts' / 'publish-release.py')])
            else:
                print(f"\nWhen you're ready:")
                print(f"  python scripts/publish-release.py")
        else:
            print(f"{Colors.RED}{Colors.BOLD}FAILED: {failed} check(s) failed{Colors.RESET}")
            print(f"Passed: {passed}/{len(checks)}")
            sys.exit(1)
    else:
        # Auto mode - simple output
        if failed == 0:
            print(f"\n✓ All checks passed ({passed}/{len(checks)})")
            sys.exit(0)
        else:
            print(f"\n✗ {failed} check(s) failed ({passed}/{len(checks)} passed)")
            sys.exit(1)


if __name__ == '__main__':
    main()
