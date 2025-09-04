#!/usr/bin/env python3
"""
DAIC command entry point for pip/pipx installations.

This module provides the console script entry point for the daic command
when cc-sessions is installed via pip or pipx. It locates the project's
.claude directory and toggles the DAIC mode.
"""

import sys
import json
from pathlib import Path


def find_project_root():
    """Find project root by looking for .claude directory."""
    current = Path.cwd()
    while current.parent != current:
        if (current / ".claude").exists():
            return current
        current = current.parent
    return None


def toggle_daic_mode():
    """Toggle DAIC mode between discussion and implementation."""
    project_root = find_project_root()
    
    if not project_root:
        print("[DAIC Error] Could not find .claude directory in current path or parent directories", file=sys.stderr)
        return 1
    
    # Import shared_state from the project's hooks directory
    hooks_dir = project_root / ".claude" / "hooks"
    if not hooks_dir.exists():
        print(f"[DAIC Error] Hooks directory not found at {hooks_dir}", file=sys.stderr)
        return 1
    
    # Add hooks directory to Python path
    sys.path.insert(0, str(hooks_dir))
    
    try:
        from shared_state import toggle_daic_mode as toggle_mode
        mode = toggle_mode()
        print(f"[DAIC] {mode}")
        return 0
    except ImportError as e:
        print(f"[DAIC Error] Could not import shared_state: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[DAIC Error] Failed to toggle mode: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the daic command."""
    sys.exit(toggle_daic_mode())


if __name__ == "__main__":
    main()