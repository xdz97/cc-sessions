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
from shared_state import load_state, edit_state, Mode, PROJECT_ROOT
##-##

#-#

# ===== GLOBALS ===== #
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
cwd = input_data.get("cwd", "")
mod = False

STATE = load_state()
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

#!> Claude compass (directory position reminder)
if tool_name == "Bash":
    command = tool_input.get("command", "")
    if "cd " in command: print(f"[You are in: {cwd}]", file=sys.stderr); mod = True
#!<

#!> Subagent cleanup
if tool_name == "Task" and STATE.flags.subagent:
    with edit_state() as s: s.flags.subagent = False; STATE = s
    # Clean up agent transcript directory
    subagent_type = tool_input.get("subagent_type", "shared")
    agent_dir = PROJECT_ROOT / 'sessions' / 'transcripts' / subagent_type
    if agent_dir.exists(): shutil.rmtree(agent_dir)
    sys.exit(0)
#!<

#!> Todo completion
if STATE.mode is Mode.GO and tool_name == "TodoWrite" and STATE.todos.all_complete():
    # Check if all complete (names already verified to match if active_todos existed)
    print("[DAIC: Todos Complete] All todos completed.\n\n", file=sys.stderr)
 
    if STATE.todos.stashed:
        with edit_state() as s: num_restored = s.todos.restore_stashed(); restored = [t.content for t in s.todos.active]; STATE = s
        # TODO: Replace printed command hint for clearing active todos with less verbose agent API (expose critical functions/methods to the agent directly with python/TS|JS script + args)
        if num_restored:
            print(f"Your previous {num_restored} todos have been restored to active and you may immediately resume completing them.\nFor reference, those todos are:\n\n{json.dumps(restored, indent=2)}\n\nIf you don't need these, just run `cd .claude/hooks && python -c \"from shared_state import edit_state; with edit_state() as s: s.todos.clear_active\"` to clear them.\n\n", file=sys.stderr)
    else:
        with edit_state() as s: s.todos.active = []; s.mode = Mode.NO; STATE = s
        print("You have returned to discussion mode. You may now discuss next steps with the user.\n\n", file=sys.stderr)
    mod = True
#!<

#!> Implementation mode + no Todos enforcement
if STATE.mode is Mode.GO and not STATE.flags.subagent and not STATE.todos.active:
    # In implementation mode but no todos - show reminder
    print("[Reminder] You're in implementation mode without approved todos. "
            "If you proposed todos that were approved, add them. "
            "If the user asked you to do something without todo proposal/approval, translate *only the remaining work* to todos and add them (all 'pending'). "
            "In any case, return to discussion mode after completing approved implementation.", file=sys.stderr)
    mod = True
#!<

#-#

if mod: sys.exit(2)  # Exit code 2 feeds stderr back to Claude
sys.exit(0)
