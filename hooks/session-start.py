#!/usr/bin/env python3
"""Session start hook to initialize Claude Code Sessions context."""
import json
import os
import sys
import subprocess
from pathlib import Path
from shared_state import get_project_root, ensure_state_dir, get_task_state

# Get project root
PROJECT_ROOT = get_project_root()

# Get developer name from config
try:
    CONFIG_FILE = PROJECT_ROOT / '.claude' / 'sessions-config.json'
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            developer_name = config.get('developer_name', 'the developer')
    else:
        developer_name = 'the developer'
except:
    developer_name = 'the developer'

# Initialize context
context = f"""You are beginning a new context window with {developer_name}.

"""

# Quick configuration checks
needs_setup = False
quick_checks = []

# 1. Check if daic command exists
try:
    result = subprocess.run(['which', 'daic'], capture_output=True, text=True, timeout=1)
    if result.returncode != 0:
        needs_setup = True
        quick_checks.append("daic command")
except:
    needs_setup = True
    quick_checks.append("daic command")

# 2. Check if tiktoken is installed (required for subagent transcript chunking)
try:
    import tiktoken
except ImportError:
    needs_setup = True
    quick_checks.append("tiktoken (pip install tiktoken)")

# 3. Check if DAIC state file exists (create if not)
ensure_state_dir()
daic_state_file = PROJECT_ROOT / '.claude' / 'state' / 'daic-mode.json'
if not daic_state_file.exists():
    # Create default state
    with open(daic_state_file, 'w') as f:
        json.dump({"mode": "discussion"}, f, indent=2)

# 4. Clear context warning flags for new session
warning_75_flag = PROJECT_ROOT / '.claude' / 'state' / 'context-warning-75.flag'
warning_90_flag = PROJECT_ROOT / '.claude' / 'state' / 'context-warning-90.flag'
if warning_75_flag.exists():
    warning_75_flag.unlink()
if warning_90_flag.exists():
    warning_90_flag.unlink()

# 5. Check if sessions directory exists
sessions_dir = PROJECT_ROOT / 'sessions'
if sessions_dir.exists():
    # Check for active task
    task_state = get_task_state()
    if task_state.get("task"):
        task_file = sessions_dir / 'tasks' / f"{task_state['task']}.md"
        if task_file.exists():
            context += f"""Active task: {task_state['task']}
Branch: {task_state['branch']}

Load the task context by reading: sessions/tasks/{task_state['task']}.md
"""
    else:
        # No active task
        context += """No active task set. Available commands:
- List tasks: ls sessions/tasks/
- Create task: Follow sessions/protocols/task-creation.md
- Start task: Follow sessions/protocols/task-startup.md
"""
else:
    # Sessions directory doesn't exist - likely first run
    context += """Sessions system is not yet initialized.

Run the install script to set up the sessions framework:
.claude/sessions-setup.sh

Or follow the manual setup in the documentation.
"""

# If setup is needed, provide guidance
if needs_setup:
    context += f"""
[Setup Required]
Missing components: {', '.join(quick_checks)}

To complete setup:
1. Run: .claude/sessions-setup.sh
2. Or manually install the daic command to /usr/local/bin/

The sessions system helps manage tasks and maintain discussion/implementation workflow discipline.
"""

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))