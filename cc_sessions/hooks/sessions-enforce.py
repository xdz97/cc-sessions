#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from typing import Optional
from pathlib import Path
import subprocess
import json
import sys
import os
import re
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from shared_state import (  check_daic_mode_bool, store_active_todos, clear_active_todos,
                            get_active_todos, get_task_state, set_daic_mode, PROJECT_ROOT,
                            USER_CONFIG, restore_stashed_todos )
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

# Check current mode
discussion_mode = check_daic_mode_bool()

expected_branch = None
affected_services = []
if not discussion_mode and tool_name in ["Write", "Edit", "MultiEdit"] and file_path:
    # Get current task details
    task_state = get_task_state()
    expected_branch = task_state.get("branch")
    affected_services = task_state.get("services", [])

if tool_name == "Bash":
    command = tool_input.get("command", "").strip()

    # Split compound commands on common shell operators
    # Split on &&, ||, ;, and | (but not ||)
    command_parts = re.split(r'(?:&&|\|\||;|\|)', command)

if tool_name == "TodoWrite":
    incoming_todos = tool_input.get("todos", [])
    active_todos = get_active_todos()
    all_complete = all(t.get('status') == 'completed' for t in incoming_todos)

## ===== PATTERNS ===== ##
modify_patterns = [ r'\brm\b', r'\bremove\b', r'\bdelete\b', r'\bmv\b', r'\bmove\b', 
                    r'\brename\b', r'\becho.*>', r'\bcat.*>', r'\btee\b', r'\bsed\b', 
                    r'\bawk\b', r'\btruncate\b', r'\btouch\b', r'\bcp\b', r'\bcopy\b' ]

# Patterns that indicate write operations
write_patterns = [  r'>\s*[^>]', r'>>', r'\btee\b', r'\bmv\b', r'\bcp\b', r'\brm\b',
                    r'\bmkdir\b', r'\btouch\b', r'\bawk\s+.*\{.*print.*>\s*["\']',
                    r'\bnpm\s+install', r'\bsed\s+(?!-n)', r'\bpip\s+install',
                    r'\bapt\s+install', r'\byum\s+install', r'\bbrew\s+install', ]

# List of read-only command prefixes that can bypass all checks
read_only_commands = [  "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
                        "grep", "rg", "find", "which", "whereis", "type", "file", "stat", "du",
                        "df", "tree", "basename", "dirname", "realpath", "readlink", "whoami",
                        "env", "printenv", "date", "cal", "uptime", "ps", "top", "wc", "cut",
                        "git remote", "git fetch", "git describe", "git rev-parse", "git blame",
                        "git status", "git log", "git diff", "git show", "git branch",
                        "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum",
                        "docker ps", "docker images", "docker logs", "npm list",
                        "npm ls", "pip list", "pip show", "yarn list", "curl",
                        "wget", "jq", "awk", "sed -n", "tar -t", "unzip -l" ]
##-##

## ===== FLAGS ===== ##
has_write_pattern = None
if tool_name == "Bash": has_write_pattern = any(re.search(pattern, command) for pattern in write_patterns)
subagent_flag = PROJECT_ROOT / 'sessions' / 'state' / 'in_subagent_context.flag'
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
# Extract just the content strings for name comparison
def get_todo_names(todos): return [t.get('content', '') for t in todos]

# Find the git repo for this file by walking up the directory tree
def find_git_repo(path: Path) -> Optional[Path]:
    """Walk up directory tree to find .git directory."""
    current = path if path.is_dir() else path.parent
    while True:
        if (current / '.git').exists(): return current
        if current == PROJECT_ROOT or current.parent == current: break
        current = current.parent
    return None
##-##

#-#

# ===== EXECUTION ===== #

# TODO: Deal with user-defined write patterns, read patterns, and other elements from the sessions-config.json config as needed

#!> Bash command handling
# For Bash commands, check if it's a read-only operation
if tool_name == "Bash":

    #!> Block any attempt to modify active-todos.json directly
    if 'active-todos.json' in command:
        # Check if it's a modifying operation
        if any(re.search(pattern, command, re.IGNORECASE) for pattern in modify_patterns):
            print("[Security] Direct modification of active-todos.json is not allowed. "
                  "This file should only be modified through the TodoWrite tool.", file=sys.stderr)
            sys.exit(2)
    #!<
 
    # TODO: Rethink this logic - we currently check for a list of write commands and block if any are found. We also check for a list of read-only commands and allow if all commands are read-only. This could lead to false positives/negatives. It also doesn't account for CLI commands that may have both read and write effects (e.g., git commands) or which may allow write operations where undesired.
    if not has_write_pattern:
        # Check if ALL commands in the chain are read-only
        all_read_only = True
        for part in command_parts:
            part = part.strip()
            if not part: continue

            # Check if this part starts with a read-only command
            is_part_read_only = any(part.startswith(prefix) for prefix in read_only_commands)
            if not is_part_read_only: all_read_only = False; has_write_pattern = True; break

        # Allow read-only commands without any checks
        if all_read_only: sys.exit(0)
#!<

#!> Block configured tools in discussion mode
if discussion_mode and (tool_name in USER_CONFIG.get("blocked_tools", ["Write", "Edit", "MultiEdit", "TodoWrite", "NotebookEdit"]) or has_write_pattern):
    print(f"[DAIC: Tool Blocked] You're in discussion mode. The {tool_name} tool is not allowed. You need to seek alignment first.", file=sys.stderr)
    sys.exit(2)  # Block with feedback
#!<

# --- All commands beyond here contain write patterns (read patterns exit early) ---

#!> TodoWrite tool handling
if tool_name == "TodoWrite":

    # Check for name mismatch first (regardless of completion state)
    if active_todos:
        active_names = get_todo_names(active_todos)
        incoming_names = get_todo_names(incoming_todos)

        if active_names != incoming_names:
            # Todo names changed - safety violation
            clear_active_todos()
            set_daic_mode(True)
            print("[DAIC: Blocked] Todo list changed - this violates agreed execution boundaries. "
                  "Previous todos cleared and returned to discussion mode. "
                  "If you need to change the task list, propose the updated version. "
                  "If this was an error, re-propose your previously planned todos.", file=sys.stderr)
            sys.exit(2)

    # Check if all complete (names already verified to match if active_todos existed)
    if all_complete:
        clear_active_todos()

        stashed_todos_file = PROJECT_ROOT / 'sessions' / 'state' / 'stashed_todos.json'
        if stashed_todos_file.exists(): 
            clear_active_todos() 
            todos = restore_stashed_todos()
            print(f"[DAIC: Todos Complete] All todos completed. Your previous todos have been restored to active and you may immediately resume completing them.\nFor reference, your new active todos are:\n{json.dumps(todos, indent=2)}")
        else: set_daic_mode(True)  # No stashed todos, just enter discussion mode
    else:
        # Store the todos (new list or update to existing)
        store_active_todos(incoming_todos)
#!<

#!> TodoList modification guard
# Get the file path being edited
if not file_path: sys.exit(0) # No file path, allow to proceed

# Block direct modification of active-todos.json via Write/Edit/MultiEdit
if tool_name in ["Write", "Edit", "MultiEdit", "NotebookEdit"] and 'active-todos.json' in str(file_path):
    print("[Security] Direct modification of active-todos.json is not allowed. "
        "This file should only be modified through the TodoWrite tool.", file=sys.stderr)
    sys.exit(2)
#!<

#!> Subagent boundary enforcement
# Check if we're in a subagent context and trying to edit sessions/state files
if subagent_flag.exists() and tool_name in ["Write", "Edit", "MultiEdit"]:
    # Check if trying to edit sessions/state files
    if 'sessions/state' in str(file_path) or 'sessions\\state' in str(file_path):
        print(f"[Subagent Boundary Violation] Subagents are NOT allowed to modify sessions/state files.", file=sys.stderr)
        print(f"Stay in your lane: You should only edit task-specific files, not system state.", file=sys.stderr)
        sys.exit(2)  # Block with feedback
#!<

#!> Git branch/task services enforcement
if not expected_branch: sys.exit(0) # No branch/task info, allow to proceed

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
    
            # Extract the service name from the repo path
            service_name = repo_path.name

            # Check both conditions: branch status and task inclusion
            branch_correct = (current_branch == expected_branch)
            in_task = (service_name in affected_services)
            if repo_path == PROJECT_ROOT: in_task = True # Root repo - always considered in task

            # Scenario 1: Everything is correct - allow to proceed
            if in_task and branch_correct: pass

            # Scenario 2: Service is in task but on wrong branch
            elif in_task and not branch_correct:
                print(f"[Branch Mismatch] Service '{service_name}' is part of this task but is on branch '{current_branch}' instead of '{expected_branch}'.", file=sys.stderr)
                print(f"Please run: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout {expected_branch}", file=sys.stderr)
                sys.exit(2)

            # Scenario 3: Service not in task but already on correct branch
            elif not in_task and branch_correct:
                print(f"[Service Not in Task] Service '{service_name}' is on the correct branch '{expected_branch}' but is not listed in the task file.", file=sys.stderr)
                print(f"Please update the task file to include '{service_name}' in the services list.", file=sys.stderr)
                sys.exit(2)

            # Scenario 4: Service not in task AND on wrong branch
            else:
                print(f"[Service Not in Task + Wrong Branch] Service '{service_name}' has two issues:", file=sys.stderr)
                print(f"  1. Not listed in the task file's services", file=sys.stderr)
                print(f"  2. On branch '{current_branch}' instead of '{expected_branch}'", file=sys.stderr)
                print(f"To fix: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout -b {expected_branch}", file=sys.stderr)
                print(f"Then update the task file to include '{service_name}' in the services list.", file=sys.stderr)
                sys.exit(2)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            # Can't check branch, allow to proceed but warn
            print(f"Warning: Could not verify branch for {repo_path.name}: {e}", file=sys.stderr)
#!<

# Old cc-sessions sessions-enforce logic kept for reference
#!> Branch enforcement for Write/Edit/MultiEdit tools (if enabled)
# branch_config = USER_CONFIG.get("branch_enforcement", DEFAULT_CONFIG["branch_enforcement"])
# if branch_config.get("enabled", True) and tool_name in ["Write", "Edit", "MultiEdit"]:
#     # Get the file path being edited
#     file_path = tool_input.get("file_path", "")
#     if file_path:
#         file_path = Path(file_path)
#         # Get current task state
#         task_state = get_task_state()
#         expected_branch = task_state.get("branch")
#         affected_services = task_state.get("services", [])
#         if expected_branch:
#             # Find the git repo for this file
#             repo_path = find_git_repo(file_path)
#             if repo_path:
#                 try:
#                     # Get current branch
#                     result = subprocess.run(
#                         ["git", "branch", "--show-current"],
#                         cwd=str(repo_path),
#                         capture_output=True,
#                         text=True,
#                         timeout=2
#                     )
#                     current_branch = result.stdout.strip()
#                     # Check if we're in a submodule
#                     try:
#                         # Try to make repo_path relative to PROJECT_ROOT
#                         repo_path.relative_to(PROJECT_ROOT)
#                         is_submodule = (repo_path != PROJECT_ROOT)
#                     except ValueError:
#                         # Not a subdirectory
#                         is_submodule = False
#                     if is_submodule:
#                         # We're in a submodule
#                         service_name = repo_path.name
#                         # Check both conditions: branch status and task inclusion
#                         branch_correct = (current_branch == expected_branch)
#                         in_task = (service_name in affected_services)
#                         # Handle all four scenarios with clear, specific error messages
#                         if in_task and branch_correct:
#                             # Scenario 1: Everything is correct - allow to proceed
#                             pass
#                         elif in_task and not branch_correct:
#                             # Scenario 2: Service is in task but on wrong branch
#                             print(f"[Branch Mismatch] Service '{service_name}' is part of this task but is on branch '{current_branch}' instead of '{expected_branch}'.", file=sys.stderr)
#                             print(f"Please run: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout {expected_branch}", file=sys.stderr)
#                             sys.exit(2)
#                         elif not in_task and branch_correct:
#                             # Scenario 3: Service not in task but already on correct branch
#                             print(f"[Service Not in Task] Service '{service_name}' is on the correct branch '{expected_branch}' but is not listed in the task file.", file=sys.stderr)
#                             print(f"Please update the task file to include '{service_name}' in the services list.", file=sys.stderr)
#                             sys.exit(2)
#                         else:  # not in_task and not branch_correct
#                             # Scenario 4: Service not in task AND on wrong branch
#                             print(f"[Service Not in Task + Wrong Branch] Service '{service_name}' has two issues:", file=sys.stderr)
#                             print(f"  1. Not listed in the task file's services", file=sys.stderr)
#                             print(f"  2. On branch '{current_branch}' instead of '{expected_branch}'", file=sys.stderr)
#                             print(f"To fix: cd {repo_path.relative_to(PROJECT_ROOT)} && git checkout -b {expected_branch}", file=sys.stderr)
#                             print(f"Then update the task file to include '{service_name}' in the services list.", file=sys.stderr)
#                             sys.exit(2)
#                     else:
#                         # Single repo or main repo
#                         if current_branch != expected_branch:
#                             print(f"[Branch Mismatch] Repository is on branch '{current_branch}' but task expects '{expected_branch}'. Please checkout the correct branch.", file=sys.stderr)
#                             sys.exit(2)
#                 except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
#                     # Can't check branch, allow to proceed but warn
#                     print(f"Warning: Could not verify branch: {e}", file=sys.stderr)
#!<

#-#

# Allow tool to proceed
sys.exit(0)
