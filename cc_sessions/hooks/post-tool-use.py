#!/usr/bin/env python3
"""Post-tool-use hook to remind about DAIC command in implementation mode."""
import json
import sys
from pathlib import Path
from shared_state import check_daic_mode_bool, get_project_root

# Load input
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
cwd = input_data.get("cwd", "")
mod = False

# Check if we're in a subagent context
project_root = get_project_root()
subagent_flag = project_root / '.claude' / 'state' / 'in_subagent_context.flag'
in_subagent = subagent_flag.exists()

# If this is the Task tool completing, clear the subagent flag
if tool_name == "Task" and in_subagent:
    subagent_flag.unlink()
    # Don't show DAIC reminder for Task completion

# Check current mode
discussion_mode = check_daic_mode_bool()

# Check for todo completion if in implementation mode (but not in subagent context)
if not discussion_mode and tool_name == "TodoWrite" and not in_subagent:
    # Check if all todos are complete
    from shared_state import check_todos_complete, set_daic_mode, clear_active_todos
    if check_todos_complete():
        set_daic_mode(True)  # Auto-return to discussion mode
        clear_active_todos()  # Clear the approved todo list
        print("[DAIC] All todos complete - returning to discussion mode", file=sys.stderr)
        mod = True

# Check for implementation mode without todos (fallback reminder)
if not discussion_mode and not in_subagent:
    from shared_state import get_active_todos
    active_todos = get_active_todos()
    if not active_todos:
        # In implementation mode but no todos - show reminder
        print("[Reminder] You're in implementation mode without approved todos. "
              "If you proposed todos that were approved, add them. "
              "If the user asked you to do something without todo proposal/approval, translate it to todos and add them. "
              "In any case, return to discussion mode after completing approved implementation.", 
              file=sys.stderr)
        mod = True

# Check for cd command in Bash operations
if tool_name == "Bash":
    command = tool_input.get("command", "")
    if "cd " in command:
        print(f"[CWD: {cwd}]", file=sys.stderr)
        mod = True

if mod:
    sys.exit(2)  # Exit code 2 feeds stderr back to Claude
else:
    sys.exit(0)# Test replay simulation - small dummy edit
