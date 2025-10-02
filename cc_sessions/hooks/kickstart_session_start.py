#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import sys
import json
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

Handles onboarding flow for new users (noob flag = true):
- Checks noob flag and exits immediately if false (lets normal hooks run)
- Respects reminder dates for "later" option
- Loads entry protocol on first run
- Resumes kickstart progress from where user left off
"""

# ===== EXECUTION ===== #

#!> 1. Load state and check noob flag
STATE = load_state()

# Not a noob? Exit immediately and let normal hooks run
if not STATE.flags.noob:
    sys.exit(0)
#!<

#!> 2. Check reminder date
reminder_date = STATE.metadata.get('kickstart_reminder_date')
if reminder_date:
    if datetime.now().isoformat() < reminder_date:
        # Still in reminder period, use normal flow
        sys.exit(0)
#!<

#!> 3. Build context based on kickstart progress
kickstart_progress = STATE.metadata.get('kickstart_progress')

if not kickstart_progress:
    # First run - load entry protocol
    context = load_protocol_file('kickstart/01-entry.md')
else:
    # Resume from where we left off
    mode = kickstart_progress.get('mode', 'full')
    current_module = kickstart_progress.get('current_module')

    context = f"[Resuming Kickstart: {mode} mode]\n\n"
    context += load_protocol_file(f'kickstart/{mode}/{current_module}.md')
#!<

#!> 4. Output context and exit
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}))
sys.exit(0)
#!<
