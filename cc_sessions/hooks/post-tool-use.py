#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import datetime
import shutil
import json
import sys
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import (  check_todos_complete, set_daic_mode, clear_active_todos,
                            check_daic_mode_bool, get_project_root, get_active_todos)
##-##

#-#

# ===== GLOBALS ===== #
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
cwd = input_data.get("cwd", "")
mod = False

# Check if we're in a subagent context
PROJECT_ROOT = get_project_root()
if tool_name == "Task": task_log = PROJECT_ROOT / 'sessions' / 'state' / 'task_tool_events.log'

## ===== FLAGS ===== ##
subagent_flag = PROJECT_ROOT / 'sessions' / 'state' / 'in_subagent_context.flag'
in_subagent = subagent_flag.exists()
discussion_mode = check_daic_mode_bool()
##-##

#-#

"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗  █████╗ ██████╗██████╗  ██████╗ █████╗  █████╗ ██╗       ██╗ ██╗██████╗██████╗ ║
║ ██╔══██╗██╔══██╗██╔═══╝╚═██╔═╝  ╚═██╔═╝██╔══██╗██╔══██╗██║       ██║ ██║██╔═══╝██╔═══╝ ║
║ ██████╔╝██║  ██║██████╗  ██║      ██║  ██║  ██║██║  ██║██║       ██║ ██║██████╗█████╗  ║
║ ██╔═══╝ ██║  ██║╚═══██║  ██║      ██║  ██║  ██║██║  ██║██║       ██║ ██║╚═══██║██╔══╝  ║
║ ██║     ╚█████╔╝██████║  ██║      ██║  ╚█████╔╝╚█████╔╝███████╗  ╚████╔╝██████║██████╗ ║
║ ╚═╝      ╚════╝ ╚═════╝  ╚═╝      ╚═╝   ╚════╝  ╚════╝ ╚══════╝   ╚═══╝ ╚═════╝╚═════╝ ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
Handles post-tool execution cleanup and state management:
- Cleans up subagent context flags and transcript directories after Task tool completion
- Auto-returns to discussion mode when all todos are marked complete
- Enforces todo-based execution boundaries in implementation mode
- Provides directory navigation feedback after cd commands
"""

# ===== EXECUTION ===== #

#!> Subagent cleanup
if tool_name == "Task" and in_subagent:
    # Clear the subagent flag
    subagent_flag.unlink()
    
    # Clean up agent transcript directory
    subagent_type = tool_input.get("subagent_type", "shared")
    agent_dir = PROJECT_ROOT / 'sessions' / 'state' / subagent_type
    
    if agent_dir.exists():
        try: shutil.rmtree(agent_dir)
        except: pass  # Ignore cleanup failures silently
#!<

#!> Todo completion (daic auto-return)
if not discussion_mode and tool_name == "TodoWrite" and not in_subagent:
    # Check if all todos are complete
    if check_todos_complete():
        set_daic_mode(True)  # Auto-return to discussion mode
        clear_active_todos()  # Clear the approved todo list
        print("[DAIC] All todos complete - returning to discussion mode", file=sys.stderr)
        mod = True
#!<

#!> Implementation mode + no Todos enforcement
if not discussion_mode and not in_subagent:
    active_todos = get_active_todos()
    if not active_todos:
        # In implementation mode but no todos - show reminder
        print("[Reminder] You're in implementation mode without approved todos. "
              "If you proposed todos that were approved, add them. "
              "If the user asked you to do something without todo proposal/approval, translate *only the remaining work* to todos and add them (all 'pending'). "
              "In any case, return to discussion mode after completing approved implementation.", 
              file=sys.stderr)
        mod = True
#!<

#!> Claude compass (directory position reminder)
if tool_name == "Bash":
    command = tool_input.get("command", "")
    if "cd " in command: print(f"[You are in: {cwd}]", file=sys.stderr); mod = True
#!<

#-#

if mod: sys.exit(2)  # Exit code 2 feeds stderr back to Claude
sys.exit(0)
