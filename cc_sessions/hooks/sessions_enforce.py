#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import subprocess, json, sys, re, shlex
from typing import Optional
from pathlib import Path
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import edit_state, load_state, Mode, PROJECT_ROOT, load_config, find_git_repo
##-##

#-#

# ===== GLOBALS ===== #
# Load input
input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

file_path = None
file_path_string = tool_input.get("file_path", "")
if file_path_string: file_path = Path(file_path_string)

STATE = load_state()
CONFIG = load_config()

if tool_name == "Bash": command = tool_input.get("command", "").strip()
if tool_name == "TodoWrite": incoming_todos = tool_input.get("todos", [])

# TODO: Write-like patterns will be extended by user config in packaged/cc-session version
## ===== PATTERNS ===== ##
READONLY_FIRST = {  'cat','less','more','grep','egrep','fgrep','head','tail','sort','uniq',
                    'cut','awk','sed','wc','printf','echo','pwd','ls','find','which','type',
                    'env','printenv','whoami','date','df','du','stat','basename','dirname','diff' }
WRITE_FIRST = {'rm','mv','cp','chmod','chown','mkdir','rmdir','ln','install','tee','truncate','touch','chattr','setfacl'}
REDIR = re.compile(r'(?:^|\s)(?:>>|>|<<?|<<<)\s')
##-##

#-#

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ ██████╗ █████╗ ██████╗ ██████╗ █████╗  █████╗ ██╗      ██╗ ██╗██████╗██████╗ ║
║ ██╔══██╗██╔═██╗██╔═══╝ ╚═██╔═╝██╔══██╗██╔══██╗██║      ██║ ██║██╔═══╝██╔═══╝ ║
║ ██████╔╝█████╔╝█████╗    ██║  ██║  ██║██║  ██║██║      ██║ ██║██████╗█████╗  ║
║ ██╔═══╝ ██╔═██╗██╔══╝    ██║  ██║  ██║██║  ██║██║      ██║ ██║╚═══██║██╔══╝  ║
║ ██║     ██║ ██║██████╗   ██║  ╚█████╔╝╚█████╔╝███████╗ ╚████╔╝██████║██████╗ ║
║ ╚═╝     ╚═╝ ╚═╝╚═════╝   ╚═╝   ╚════╝  ╚════╝ ╚══════╝  ╚═══╝ ╚═════╝╚═════╝ ║
╚══════════════════════════════════════════════════════════════════════════════╝
PreToolUse Hook

Trigger conditions:
- Write/subagent tool invocation (Bash, Write, Edit, MultiEdit, Task, TodoWrite)

Enforces DAIC (Discussion, Alignment, Implementation, Check) workflow:
- Blocks write tools in discussion mode
- Validates TodoWrite operations for proper scope management
- Enforces git branch consistency with task requirements
- Protects system state files from unauthorized modification
"""

# ===== FUNCTIONS ===== #

## ===== HELPERS ===== ##
# Check if a bash command is read-only (no writes, no redirections)
def is_bash_read_only(command: str, extrasafe: bool = CONFIG.blocked_actions.extrasafe or True) -> bool:
    """Determine if a bash command is read-only.
    Args:
        command (str): The bash command to evaluate.
        extrasafe (bool): If True, unrecognized commands are treated as write-like."""
    s = (command or '').strip()
    if not s: return True
    if REDIR.search(s): return False
    for segment in re.split(r'[|]{1,2}|&&|\|\|', s):
        segment = segment.strip()
        if not segment: continue
        try: parts = shlex.split(segment)
        except ValueError: return not CONFIG.blocked_actions.extrasafe
        if not parts: continue
        first = parts[0].lower()
        if first == 'cd': continue
        if first in WRITE_FIRST: return False
        if CONFIG.blocked_actions.matches_custom_pattern(first): return False
        if first not in READONLY_FIRST and CONFIG.blocked_actions.extrasafe: return False
    return True
##-##

#-#

# ===== EXECUTION ===== #

#!> Bash command handling
# For Bash commands, check if it's a read-only operation
if tool_name == "Bash" and STATE.mode is Mode.NO:
    # Special case: Allow sessions.api commands in discussion mode
    if command and ('python -m sessions.api' in command or 'python -m cc_sessions.scripts.api' in command):
        # API commands are allowed in discussion mode for state inspection and safe config operations
        sys.exit(0)
    
    if not is_bash_read_only(command):
        print("[DAIC] Blocked write-like Bash command in Discussion mode. Switch to Implementation or explain what you intend to change.", file=sys.stderr); sys.exit(2)
    else: sys.exit(0)
#!<

#!> Block any attempt to modify sessions-state.json directly
if file_path and all([
    tool_name == "Bash",
    file_path.name == 'sessions-state.json',
    file_path.parent.name == 'sessions']):
    # Check if it's a modifying operation
    if not is_bash_read_only(command):
        print("[Security] Direct modification of sessions-state.json is not allowed. "
                "This file should only be modified through the TodoWrite tool and approved commands.", file=sys.stderr); sys.exit(2)
#!<
 
# --- All commands beyond here contain write patterns (read patterns exit early) ---

#!> Discussion mode guard (block write tools)
if STATE.mode is Mode.NO:
    if CONFIG.blocked_actions.is_tool_blocked(tool_name):
        print(f"[DAIC: Tool Blocked] You're in discussion mode. The {tool_name} tool is not allowed. You need to seek alignment first.", file=sys.stderr)
        sys.exit(2)  # Block with feedback
    else: sys.exit(0)  # Allow read-only tools
#!<

#!> TodoWrite tool handling
if tool_name == "TodoWrite":
    # Check for name mismatch first (regardless of completion state)
    if STATE.todos.active:
        active_names = STATE.todos.list_content('active')
        incoming_names = [t.get('content','') for t in incoming_todos]

        if active_names != incoming_names:
            # Todo names changed - safety violation
            with edit_state() as s: s.todos.clear_active(); s.mode = Mode.NO; STATE = s
            print("[DAIC: Blocked] Todo list changed - this violates agreed execution boundaries. "
                  "Previous todos cleared and returned to discussion mode. "
                  "If you need to change the task list, propose the updated version. "
                  "If this was an error, re-propose your previously planned todos.", file=sys.stderr)
            sys.exit(2)

    with edit_state() as s: 
        if not s.todos.store_todos(incoming_todos): print("[TodoWrite Error] Failed to store todos - check format", file=sys.stderr); sys.exit(2)
        else: STATE = s
#!<

#!> TodoList modification guard
# Get the file path being edited
if not file_path: sys.exit(0) # No file path, allow to proceed

# Block direct modification of state file via Write/Edit/MultiEdit
if all([    tool_name in ["Write", "Edit", "MultiEdit", "NotebookEdit"],
            file_path.name == 'sessions-state.json',
            file_path.parent.name == 'sessions' ]):
    print("[Security] Direct modification of sessions-state.json is not allowed. "
        "This file should only be modified through the TodoWrite tool and approved commands.", file=sys.stderr)
    sys.exit(2)
#!<

#!> Git branch/task submodules enforcement
if not (expected_branch := STATE.current_task.branch): sys.exit(0) # No branch/task info, allow to proceed

else:
    repo_path = find_git_repo(file_path)

    if repo_path:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=2
            )
            current_branch = result.stdout.strip()
    
            # Extract the submodule name from the repo path
            submodule_name = repo_path.name

            # Check both conditions: branch status and task inclusion
            branch_correct = (current_branch == expected_branch)
            in_task = (STATE.current_task.submodules and submodule_name in STATE.current_task.submodules)
            if repo_path == PROJECT_ROOT: in_task = True # Root repo - always considered in task

            # Scenario 1: Everything is correct - allow to proceed
            if in_task and branch_correct: pass

            # Scenario 2: Submodule is in task but on wrong branch
            elif in_task and not branch_correct:
                print(f"[Branch Mismatch] Submodule '{submodule_name}' is part of this task but is on branch '{current_branch}' instead of '{expected_branch}'.", file=sys.stderr)
                print(f"Please run: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout {expected_branch}", file=sys.stderr)
                sys.exit(2)

            # Scenario 3: Submodule not in task but already on correct branch
            elif not in_task and branch_correct:
                print(f"[Submodule Not in Task] Submodule '{submodule_name}' is on the correct branch '{expected_branch}' but is not listed in the task file.", file=sys.stderr)
                print(f"Please update the task file to include '{submodule_name}' in the submodules list.", file=sys.stderr)
                sys.exit(2)

            # Scenario 4: Submodule not in task AND on wrong branch
            else:
                print(f"[Submodule Not in Task + Wrong Branch] Submodule '{submodule_name}' has two issues:", file=sys.stderr)
                print(f"  1. Not listed in the task file's submodules", file=sys.stderr)
                print(f"  2. On branch '{current_branch}' instead of '{expected_branch}'", file=sys.stderr)
                print(f"To fix: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout -b {expected_branch}", file=sys.stderr)
                print(f"Then update the task file to include '{submodule_name}' in the submodules list.", file=sys.stderr)
                sys.exit(2)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            # Can't check branch, allow to proceed but warn
            print(f"Warning: Could not verify branch for {repo_path.name}: {e}", file=sys.stderr)
#!<

#-#

# Allow tool to proceed
sys.exit(0)
