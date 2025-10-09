#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import sys
import json
import os
from datetime import datetime
from pathlib import Path
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
# Import from shared_state (same pattern as normal hooks)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'sessions' / 'hooks'))
from shared_state import load_state
##-##

#-#

# ===== GLOBALS ===== #

## ===== CI DETECTION ===== ##
def is_ci_environment():
    """Check if running in a CI environment (GitHub Actions)."""
    ci_indicators = [
        'GITHUB_ACTIONS',         # GitHub Actions
        'GITHUB_WORKFLOW',        # GitHub Actions workflow
        'CI',                     # Generic CI indicator (set by GitHub Actions)
        'CONTINUOUS_INTEGRATION', # Generic CI (alternative)
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)

# Skip kickstart session start hook in CI environments
if is_ci_environment():
    sys.exit(0)
##-##

## ===== MODULE SEQUENCES ===== ##
FULL_MODE_SEQUENCE = [
    '01-discussion.md',
    '02-implementation.md',
    '03-tasks-overview.md',
    '04-task-creation.md',
    '05-task-startup.md',
    '06-task-completion.md',
    '07-compaction.md',
    '08-agents.md',
    '09-api.md',
    '10-advanced.md',
    '11-graduation.md'
]

SUBAGENTS_MODE_SEQUENCE = [
    '01-agents-only.md'
]
##-##

#-#

# ===== FUNCTIONS ===== #

def load_protocol_file(relative_path: str) -> str:
    """Load protocol markdown from protocols directory."""
    protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / relative_path
    if not protocol_path.exists():
        return f"Error: Protocol file not found: {relative_path}"
    return protocol_path.read_text()

#-#

"""
Kickstart SessionStart Hook

Handles onboarding flow for users who chose kickstart in installer:
- Checks for kickstart metadata (should ALWAYS exist if this hook is running)
- Loads first module on first run, resumes from current_index on subsequent runs
- Sequences determined by mode (full or subagents)
"""

# ===== EXECUTION ===== #

#!> 1. Load state and check kickstart metadata
STATE = load_state()

# Get kickstart metadata (should ALWAYS exist if this hook is running)
kickstart_meta = STATE.metadata.get('kickstart')
if not kickstart_meta:
    # This is a BUG - fail loudly
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "ERROR: kickstart_session_start hook fired but no kickstart metadata found. This is an installer bug."
        }
    }))
    sys.exit(1)

mode = kickstart_meta.get('mode')  # 'full' or 'subagents'
if not mode:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "ERROR: kickstart metadata exists but no mode specified. This is an installer bug."
        }
    }))
    sys.exit(1)
#!<

#!> 2. Initialize or load sequence
# Determine sequence based on mode
if mode == 'full':
    sequence = FULL_MODE_SEQUENCE
elif mode == 'subagents':
    sequence = SUBAGENTS_MODE_SEQUENCE
else:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"ERROR: Invalid kickstart mode '{mode}'. Expected 'full' or 'subagents'."
        }
    }))
    sys.exit(1)

# Initialize sequence on first run
if 'sequence' not in kickstart_meta:
    from shared_state import edit_state
    with edit_state() as s:
        s.metadata['kickstart']['sequence'] = sequence
        s.metadata['kickstart']['current_index'] = 0
        s.metadata['kickstart']['completed'] = []

    protocol_content = load_protocol_file(f'kickstart/{sequence[0]}')
else:
    # Load current protocol from sequence
    current_index = kickstart_meta.get('current_index', 0)
    protocol_content = load_protocol_file(f'kickstart/{sequence[current_index]}')
#!<

#!> 3. Append user instructions and output
protocol_content += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INSTRUCTIONS:
Just say 'kickstart' and press enter to begin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": protocol_content
    }
}))
sys.exit(0)
#!<
