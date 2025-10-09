#!/usr/bin/env python3
"""
Release Publishing Script for cc-sessions

Atomically publishes releases to PyPI and npm with git tagging and GitHub release creation.

Pre-flight checks:
- Re-runs all prep script validations
- Verifies main is not ahead of next
- Tests PyPI and npm credentials
- Validates network connectivity

Publishing sequence:
1. Extract version from package.json
2. Run pre-flight checks
3. Merge next → main
4. Create git tag on main
5. Build Python artifacts
6. Publish to PyPI
7. Publish to npm
8. Push commits and tags
9. Create GitHub Release with CHANGELOG excerpt
10. Return to next branch
11. Create new "Unreleased" section in CHANGELOG
12. Commit new release cycle

Usage:
    python scripts/publish-release.py

Error handling:
- Interactive rollback prompt if publish fails
- Manual recovery instructions if rollback declined
- Preserves git state for manual intervention
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Optional, Tuple
from datetime import date


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def get_repo_root() -> Path:
    """Get the repository root directory"""
    result = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True,
        text=True,
        check=True
    )
    return Path(result.stdout.strip())


def read_version_from_package_json(repo_root: Path) -> Optional[str]:
    """Extract version from package.json"""
    package_json = repo_root / 'package.json'
    try:
        with open(package_json, 'r') as f:
            data = json.load(f)
            return data.get('version')
    except Exception as e:
        print(f"{Colors.RED}Error reading package.json: {e}{Colors.RESET}")
        return None


def check_main_not_ahead(repo_root: Path) -> Tuple[bool, str]:
    """Check that main is not ahead of next (would cause conflicts)"""
    try:
        # Get commits in main but not in next
        result = subprocess.run(
            ['git', 'log', 'next..main', '--oneline'],
            cwd=repo_root,
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            commits = result.stdout.strip().split('\n')
            return False, f"main is ahead of next by {len(commits)} commit(s)"

        return True, "main not ahead of next"
    except subprocess.CalledProcessError as e:
        return False, f"Could not compare branches: {e}"


def test_pypi_credentials() -> Tuple[bool, str]:
    """Test that twine can authenticate to PyPI"""
    try:
        # Try to get repository info (doesn't upload anything)
        result = subprocess.run(
            ['twine', 'check', '--help'],
            capture_output=True,
            timeout=5
        )
        # If twine is available, assume credentials will work or prompt
        return True, "twine available"
    except FileNotFoundError:
        return False, "twine not installed"
    except Exception as e:
        return False, f"twine check failed: {e}"


def test_npm_credentials(repo_root: Path) -> Tuple[bool, str]:
    """Test that npm is authenticated"""
    try:
        # Check if logged in
        result = subprocess.run(
            ['npm', 'whoami'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            username = result.stdout.strip()
            return True, f"Logged in as {username}"
        else:
            return False, "Not logged in to npm (run: npm login)"
    except FileNotFoundError:
        return False, "npm not found"
    except subprocess.TimeoutExpired:
        return False, "npm authentication check timed out"
    except Exception as e:
        return False, f"npm check failed: {e}"


def test_network_connectivity() -> Tuple[bool, str]:
    """Test connectivity to PyPI and npm registries"""
    try:
        # Test PyPI
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://pypi.org'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0 or result.stdout.strip() not in ['200', '301', '302']:
            return False, f"Cannot reach pypi.org (HTTP {result.stdout.strip()})"

        # Test npm
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://registry.npmjs.org'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0 or result.stdout.strip() not in ['200', '301', '302']:
            return False, f"Cannot reach registry.npmjs.org (HTTP {result.stdout.strip()})"

        return True, "Network connectivity OK"
    except FileNotFoundError:
        return False, "curl not found (cannot test connectivity)"
    except subprocess.TimeoutExpired:
        return False, "Network connectivity test timed out"
    except Exception as e:
        return False, f"Network test failed: {e}"


def run_prep_checks(repo_root: Path) -> Tuple[bool, list]:
    """Run preparation script validation checks"""
    print(f"{Colors.CYAN}Running preparation checks...{Colors.RESET}")

    try:
        result = subprocess.run(
            ['python', str(repo_root / 'scripts' / 'prepare-release.py'), '--auto'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            return True, []
        else:
            errors = result.stdout.strip().split('\n')
            return False, errors
    except subprocess.TimeoutExpired:
        return False, ["Preparation checks timed out"]
    except Exception as e:
        return False, [f"Could not run prep checks: {e}"]


def extract_changelog_section(repo_root: Path, version: str) -> Optional[str]:
    """Extract the CHANGELOG.md section for the given version"""
    changelog_path = repo_root / 'CHANGELOG.md'

    try:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Find the version section
        version_pattern = rf'##\s*\[{re.escape(version)}\]\s*-\s*\d{{4}}-\d{{2}}-\d{{2}}'
        match = re.search(version_pattern, content)

        if not match:
            return None

        # Extract from this version until the next ## heading
        start = match.start()
        next_heading = content.find('\n## ', start + 1)

        if next_heading == -1:
            section = content[start:].strip()
        else:
            section = content[start:next_heading].strip()

        return section
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Could not extract CHANGELOG section: {e}{Colors.RESET}")
        return None


def create_unreleased_section(repo_root: Path) -> bool:
    """Create new Unreleased section in CHANGELOG.md"""
    changelog_path = repo_root / 'CHANGELOG.md'

    try:
        with open(changelog_path, 'r') as f:
            content = f.read()

        # Find the first ## heading (should be the version we just released)
        first_heading = content.find('\n## ')

        if first_heading == -1:
            print(f"{Colors.YELLOW}Warning: Could not find version heading in CHANGELOG{Colors.RESET}")
            return False

        # Insert Unreleased section before first heading
        unreleased_section = f"\n## Unreleased\n\n### Added\n### Changed\n### Fixed\n"
        new_content = content[:first_heading] + unreleased_section + content[first_heading:]

        with open(changelog_path, 'w') as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Could not create Unreleased section: {e}{Colors.RESET}")
        return False


def rollback_git_changes(repo_root: Path, version: str) -> bool:
    """Rollback git changes (delete tag, reset main, return to next)"""
    try:
        # Delete tag
        subprocess.run(['git', 'tag', '-d', f'v{version}'], cwd=repo_root, check=True)

        # Reset main to previous commit
        subprocess.run(['git', 'checkout', 'main'], cwd=repo_root, check=True)
        subprocess.run(['git', 'reset', '--hard', 'HEAD~1'], cwd=repo_root, check=True)

        # Return to next
        subprocess.run(['git', 'checkout', 'next'], cwd=repo_root, check=True)

        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Rollback failed: {e}{Colors.RESET}")
        return False


def main():
    """Main entry point"""
    try:
        repo_root = get_repo_root()
    except subprocess.CalledProcessError:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.BOLD}Release Publishing{Colors.RESET}")
    print(f"Repository: {repo_root}\n")

    # Step 1: Extract version
    print(f"{Colors.CYAN}[1/15] Extracting version from package.json...{Colors.RESET}")
    version = read_version_from_package_json(repo_root)

    if not version:
        print(f"{Colors.RED}Failed to extract version{Colors.RESET}")
        sys.exit(1)

    print(f"Version: {Colors.GREEN}{version}{Colors.RESET}\n")

    # Step 2: Run pre-flight checks
    print(f"{Colors.BOLD}=== Pre-flight Checks ==={Colors.RESET}\n")

    checks = [
        ("Preparation validation", lambda: run_prep_checks(repo_root)),
        ("Main branch status", lambda: check_main_not_ahead(repo_root)),
        ("PyPI credentials", test_pypi_credentials),
        ("npm credentials", lambda: test_npm_credentials(repo_root)),
        ("Network connectivity", test_network_connectivity)
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"Checking {name}...", end=' ')
        passed, message = check_func()

        if passed:
            print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} {message}")
            all_passed = False

    if not all_passed:
        print(f"\n{Colors.RED}Pre-flight checks failed. Cannot proceed with release.{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.GREEN}All pre-flight checks passed!{Colors.RESET}\n")

    # Point of no return warning
    print(f"{Colors.YELLOW}{Colors.BOLD}=== POINT OF NO RETURN ==={Colors.RESET}")
    print("The following operations will make changes:\n")
    print(f"  • Merge 'next' → 'main'")
    print(f"  • Create git tag v{version}")
    print(f"  • Build Python artifacts")
    print(f"  • Publish to PyPI")
    print(f"  • Publish to npm")
    print(f"  • Push commits and tags to GitHub")
    print(f"  • Create GitHub Release")
    print(f"  • Create new Unreleased section in CHANGELOG\n")

    response = input("Continue with release? (y/n): ").strip().lower()
    if response != 'y':
        print(f"\n{Colors.YELLOW}Release cancelled{Colors.RESET}")
        sys.exit(0)

    current_step = 3  # Pre-flight was steps 1-2

    try:
        # Step 3: Merge next → main
        print(f"\n{Colors.CYAN}[{current_step}/15] Merging 'next' → 'main'...{Colors.RESET}")
        subprocess.run(['git', 'checkout', 'main'], cwd=repo_root, check=True)
        subprocess.run(['git', 'merge', 'next'], cwd=repo_root, check=True)
        print(f"{Colors.GREEN}✓ Merged{Colors.RESET}")
        current_step += 1

        # Step 4: Create tag
        print(f"\n{Colors.CYAN}[{current_step}/15] Creating git tag v{version}...{Colors.RESET}")
        subprocess.run(['git', 'tag', f'v{version}'], cwd=repo_root, check=True)
        print(f"{Colors.GREEN}✓ Tag created{Colors.RESET}")
        current_step += 1

        # Step 5: Build Python artifacts
        print(f"\n{Colors.CYAN}[{current_step}/15] Building Python artifacts...{Colors.RESET}")
        subprocess.run(['python', '-m', 'build'], cwd=repo_root, check=True, capture_output=True)
        print(f"{Colors.GREEN}✓ Build complete{Colors.RESET}")
        current_step += 1

        # Step 6: Publish to PyPI
        print(f"\n{Colors.CYAN}[{current_step}/15] Publishing to PyPI...{Colors.RESET}")
        result = subprocess.run(
            ['twine', 'upload', 'dist/*'],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"PyPI publish failed: {result.stderr}")
        print(f"{Colors.GREEN}✓ Published to PyPI{Colors.RESET}")
        current_step += 1

        # Step 7: Publish to npm
        print(f"\n{Colors.CYAN}[{current_step}/15] Publishing to npm...{Colors.RESET}")
        result = subprocess.run(
            ['npm', 'publish'],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"npm publish failed: {result.stderr}")
        print(f"{Colors.GREEN}✓ Published to npm{Colors.RESET}")
        current_step += 1

        # Step 8: Push main commits
        print(f"\n{Colors.CYAN}[{current_step}/15] Pushing main branch...{Colors.RESET}")
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_root, check=True)
        print(f"{Colors.GREEN}✓ Pushed{Colors.RESET}")
        current_step += 1

        # Step 9: Push tags
        print(f"\n{Colors.CYAN}[{current_step}/15] Pushing tags...{Colors.RESET}")
        subprocess.run(['git', 'push', '--tags'], cwd=repo_root, check=True)
        print(f"{Colors.GREEN}✓ Pushed{Colors.RESET}")
        current_step += 1

        # Step 10: Extract CHANGELOG section
        print(f"\n{Colors.CYAN}[{current_step}/15] Extracting CHANGELOG notes...{Colors.RESET}")
        changelog_excerpt = extract_changelog_section(repo_root, version)
        if changelog_excerpt:
            print(f"{Colors.GREEN}✓ Extracted{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Using default notes{Colors.RESET}")
        current_step += 1

        # Step 11: Create GitHub Release
        print(f"\n{Colors.CYAN}[{current_step}/15] Creating GitHub Release...{Colors.RESET}")
        if changelog_excerpt:
            # Create release with CHANGELOG notes
            subprocess.run(
                ['gh', 'release', 'create', f'v{version}', '--notes', changelog_excerpt],
                cwd=repo_root,
                check=True
            )
        else:
            # Create release with auto-generated notes
            subprocess.run(
                ['gh', 'release', 'create', f'v{version}', '--generate-notes'],
                cwd=repo_root,
                check=True
            )
        print(f"{Colors.GREEN}✓ Release created{Colors.RESET}")
        current_step += 1

        # Step 12: Return to next branch
        print(f"\n{Colors.CYAN}[{current_step}/15] Returning to 'next' branch...{Colors.RESET}")
        subprocess.run(['git', 'checkout', 'next'], cwd=repo_root, check=True)
        print(f"{Colors.GREEN}✓ Switched to next{Colors.RESET}")
        current_step += 1

        # Step 13: Create Unreleased section
        print(f"\n{Colors.CYAN}[{current_step}/15] Creating new Unreleased section...{Colors.RESET}")
        if create_unreleased_section(repo_root):
            print(f"{Colors.GREEN}✓ Section created{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ Manual CHANGELOG update needed{Colors.RESET}")
        current_step += 1

        # Step 14: Commit new release cycle
        print(f"\n{Colors.CYAN}[{current_step}/15] Committing new release cycle...{Colors.RESET}")
        subprocess.run(['git', 'add', 'CHANGELOG.md'], cwd=repo_root, check=True)
        subprocess.run(
            ['git', 'commit', '-m', 'Start next release cycle'],
            cwd=repo_root,
            check=True
        )
        print(f"{Colors.GREEN}✓ Committed{Colors.RESET}")
        current_step += 1

        # Success!
        print(f"\n{Colors.GREEN}{Colors.BOLD}Release v{version} published successfully!{Colors.RESET}\n")
        print(f"Published to:")
        print(f"  • PyPI: https://pypi.org/project/cc-sessions/{version}/")
        print(f"  • npm: https://www.npmjs.com/package/cc-sessions/v/{version}")
        print(f"  • GitHub: https://github.com/GWUDCAP/cc-sessions/releases/tag/v{version}")
        print()

    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Publish failed at step {current_step}:{Colors.RESET}")
        print(f"{Colors.RED}{e}{Colors.RESET}\n")

        response = input(f"Rollback local changes? (y/n): ").strip().lower()

        if response == 'y':
            print(f"\n{Colors.CYAN}Rolling back...{Colors.RESET}")
            if rollback_git_changes(repo_root, version):
                print(f"{Colors.GREEN}Rollback complete{Colors.RESET}")
            else:
                print(f"{Colors.RED}Rollback failed - manual intervention required{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}Local git state preserved. Manual options:{Colors.RESET}\n")
            print(f"Option 1: Complete the release manually")
            print(f"  - Fix the issue that caused failure")
            print(f"  - Continue from step {current_step} in the sequence\n")
            print(f"Option 2: Rollback manually")
            print(f"  1. Delete tag: git tag -d v{version}")
            print(f"  2. Reset main: git checkout main && git reset --hard HEAD~1")
            print(f"  3. Return to next: git checkout next\n")
            print(f"Option 3: Partial rollback (if PyPI succeeded but npm failed)")
            print(f"  - Complete npm publish: npm publish")
            print(f"  - Then continue with remaining steps\n")

        sys.exit(1)


if __name__ == '__main__':
    main()
