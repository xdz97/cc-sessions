#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import json
import sys
import os
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
##-##

#-#

# ===== GLOBALS ===== #
PROJECT_ROOT = None
if project_root := os.getenv("CLAUDE_PROJECT_DIR"): PROJECT_ROOT = Path(project_root)
else:
    current = Path.cwd()
    while current.parent != current:
        if (current / ".claude").exists(): PROJECT_ROOT = current; break
        current = current.parent

if not PROJECT_ROOT:
    print("Error: Could not find project root (no .claude directory).", file=sys.stderr)
    sys.exit(2)

STATE_DIR = PROJECT_ROOT / "sessions" / "state"
DAIC_STATE_FILE = STATE_DIR / "daic-mode.json"
TASK_STATE_FILE = STATE_DIR / "current-task.json"
ACTIVE_TODOS_FILE = STATE_DIR / "active-todos.json"
STASHED_TODOS_FILE = STATE_DIR / "stashed-todos.json"

# Load configuration from project's .claude directory
CONFIG_FILE = PROJECT_ROOT / "sessions" / "sessions-config.json"

#!> Default configuration
DEFAULT_CONFIG = {
    "trigger_phrases": ["make it so", "run that"],
    "blocked_tools": ["Edit", "Write", "MultiEdit", "NotebookEdit"],
    "branch_enforcement": {
        "enabled": True,
        "task_prefixes": ["implement-", "fix-", "refactor-", "migrate-", "test-", "docs-"],
        "branch_prefixes": {
            "implement-": "feature/",
            "fix-": "fix/",
            "refactor-": "feature/",
            "migrate-": "feature/",
            "test-": "feature/",
            "docs-": "feature/"
        }
    },
    "read_only_bash_commands": [
        "ls", "ll", "pwd", "cd", "echo", "cat", "head", "tail", "less", "more",
        "grep", "rg", "find", "which", "whereis", "type", "file", "stat",
        "du", "df", "tree", "basename", "dirname", "realpath", "readlink",
        "whoami", "env", "printenv", "date", "cal", "uptime", "ps", "top",
        "wc", "cut", "sort", "uniq", "comm", "diff", "cmp", "md5sum", "sha256sum",
        "git status", "git log", "git diff", "git show", "git branch", 
        "git remote", "git fetch", "git describe", "git rev-parse", "git blame",
        "docker ps", "docker images", "docker logs", "npm list", "npm ls",
        "pip list", "pip show", "yarn list", "curl", "wget", "jq", "awk",
        "sed -n", "tar -t", "unzip -l",
        # Windows equivalents
        "dir", "where", "findstr", "fc", "comp", "certutil -hashfile",
        "Get-ChildItem", "Get-Location", "Get-Content", "Select-String",
        "Get-Command", "Get-Process", "Get-Date", "Get-Item"
    ]
}
#!<

USER_CONFIG = DEFAULT_CONFIG
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, 'r') as f: USER_CONFIG = json.load(f)
    except: pass

# Mode description strings
DISCUSSION_MODE_MSG = "You are now in Discussion Mode and should focus on discussing and investigating with the user (no edit-based tools)"
IMPLEMENTATION_MODE_MSG = "You are now in Implementation Mode and may use tools to execute the agreed upon actions - when you are done return immediately to Discussion Mode"
#-#

"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗██╗  ██╗ █████╗ █████╗ ██████╗█████╗       ██████╗██████╗ █████╗ ██████╗██████╗ ║
║ ██╔═══╝██║  ██║██╔══██╗██╔═██╗██╔═══╝██╔═██╗      ██╔═══╝╚═██╔═╝██╔══██╗╚═██╔═╝██╔═══╝ ║
║ ██████╗███████║███████║█████╔╝█████╗ ██║ ██║      ██████╗  ██║  ███████║  ██║  █████╗  ║
║ ╚═══██║██╔══██║██╔══██║██╔═██╗██╔══╝ ██║ ██║      ╚═══██║  ██║  ██╔══██║  ██║  ██╔══╝  ║
║ ██████║██║  ██║██║  ██║██║ ██║██████╗█████╔╝      ██████║  ██║  ██║  ██║  ██║  ██████╗ ║
║ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═╝╚═════╝╚════╝       ╚═════╝  ╚═╝  ╚═╝  ╚═╝  ╚═╝  ╚═════╝ ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
SharedState Module

Provides centralized state management for hooks:
- DAIC mode tracking and toggling
- Task state persistence  
- Active todo list management
- Project root detection
"""

# ===== DECLARATIONS ===== #
# Lets make a task state dataclass to deal with parsed frontmatter as an object
@dataclass
class TaskState:
    task: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None
    updated: Optional[str] = None
    submodules: Optional[list] = None
#-#

# ===== FUNCTIONS ===== #

## ===== HELPERS ===== ##
def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def get_current_model():
    """Get the current Claude model being used in sessions from the state file stored by the statusline bash script"""
    model_file = STATE_DIR / "current_model.json"
    try:
        with open(model_file, 'r') as f:
            data = json.load(f)
        model = data.get("model", "Opus 4.1")
        if "opus" in model.lower(): return "opus"
        elif "sonnet" in model.lower(): return "sonnet"
        else: return "unknown"
    except (FileNotFoundError, json.JSONDecodeError):
        return "claude-2"
##-##

## ===== DAIC MGMT ===== ##
def check_daic_mode_bool() -> bool:
    """Check if DAIC (discussion) mode is enabled. Returns True for discussion, False for implementation."""
    ensure_state_dir()
    try:
        with open(DAIC_STATE_FILE, 'r') as f:
            data = json.load(f)
            return data.get("mode", "discussion") == "discussion"
    except (FileNotFoundError, json.JSONDecodeError):
        # Default to discussion mode if file doesn't exist
        set_daic_mode(True)
        return True

def check_daic_mode() -> str:
    """Check if DAIC (discussion) mode is enabled. Returns mode message."""
    ensure_state_dir()
    try:
        with open(DAIC_STATE_FILE, 'r') as f:
            data = json.load(f)
            mode = data.get("mode", "discussion")
            return DISCUSSION_MODE_MSG if mode == "discussion" else IMPLEMENTATION_MODE_MSG
    except (FileNotFoundError, json.JSONDecodeError):
        # Default to discussion mode if file doesn't exist
        set_daic_mode(True)
        return DISCUSSION_MODE_MSG

def toggle_daic_mode() -> str:
    """Toggle DAIC mode and return the new state message."""
    ensure_state_dir()
    # Read current mode
    try:
        with open(DAIC_STATE_FILE, 'r') as f:
            data = json.load(f)
            current_mode = data.get("mode", "discussion")
    except (FileNotFoundError, json.JSONDecodeError): current_mode = "discussion"

    # Toggle and write new value
    new_mode = "implementation" if current_mode == "discussion" else "discussion"
    with open(DAIC_STATE_FILE, 'w') as f:
        json.dump({"mode": new_mode}, f, indent=2)

    # If switching to discussion, clear active todos
    if new_mode == "discussion":
        clear_active_todos()

    # Return appropriate message
    return IMPLEMENTATION_MODE_MSG if new_mode == "implementation" else DISCUSSION_MODE_MSG

def set_daic_mode(value: str|bool):
    """Set DAIC mode to a specific value."""
    ensure_state_dir()
    if value == True or value == "discussion":
        mode = "discussion"
        name = "Discussion Mode"
    elif value == False or value == "implementation":
        mode = "implementation"
        name = "Implementation Mode"
    else:
        raise ValueError(f"Invalid mode value: {value}")

    with open(DAIC_STATE_FILE, 'w') as f:
        json.dump({"mode": mode}, f, indent=2)
    return name
##-##

## ===== TASK/GIT MGMT ===== ##
def parse_task_frontmatter(content: str) -> TaskState:
    """Parse YAML frontmatter from task file content."""
    if not content.startswith('---'): return TaskState()

    lines = content.split('\n')
    frontmatter_lines = []
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line == '---': in_frontmatter = True; continue
        if in_frontmatter and line == '---': break
        if in_frontmatter: frontmatter_lines.append(line)

    # Parse the frontmatter
    frontmatter = {}
    for line in frontmatter_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle list values [item1, item2]
            if value.startswith('[') and value.endswith(']'):
                # Parse as list
                items = value[1:-1].split(',')
                value = [item.strip() for item in items]

            frontmatter[key] = value

    return TaskState(**frontmatter)

def get_active_task_name() -> Optional[str]:
    """Get the currently active task name from current-task.json."""
    try:
        with open(TASK_STATE_FILE, 'r') as f:
            data = json.load(f)
            # Support both old format (full state) and new format (just task name)
            if isinstance(data, dict): return data.get("task", None)
            return None
    except (FileNotFoundError, json.JSONDecodeError): return None

def get_task_state() -> dict:
    """Get current task state including branch and affected submodules.

    Reads task name from current-task.json, then loads full state from task file frontmatter.
    """
    # Get the active task file/file path
    task_file = get_active_task_name()
    if not task_file: return {"task": None, "branch": None, "updated": None}

    task_state = TaskState(task=task_file)

    # Find the task file
    tasks_dir = PROJECT_ROOT / "sessions" / "tasks"
    task_file_path = tasks_dir / task_file

    if task_file_path.exists():
        # Parse frontmatter
        content = task_file_path.read_text()
        frontmatter = parse_task_frontmatter(content)
        return {**frontmatter.__dict__, **task_state.__dict__}
    else: return {**task_state.__dict__}

## ===== TODO MGMT ===== ##
def get_active_todos() -> list:
    """Get the currently active/approved todos."""
    try:
        with open(ACTIVE_TODOS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("todos", [])
    except (FileNotFoundError, json.JSONDecodeError): return []

def store_active_todos(todos: list) -> None:
    """Store the approved todo list as active execution scope."""
    ensure_state_dir()
    data = {"todos": todos}
    with open(ACTIVE_TODOS_FILE, 'w') as f: json.dump(data, f, indent=2)

def clear_active_todos() -> None:
    """Clear the active todos when returning to discussion mode."""
    if ACTIVE_TODOS_FILE.exists(): ACTIVE_TODOS_FILE.unlink()

def check_todos_complete() -> bool:
    """Check if all todos in the active list are complete."""
    todos = get_active_todos()
    if not todos: return False
 
    # All todos must have status == 'completed'
    return all(t.get('status') == 'completed' for t in todos)

def stash_active_todos() -> None:
    """Stash the current active todos to a timestamped backup file."""
    todos = get_active_todos()
    if not todos: return

    with open(STASHED_TODOS_FILE, 'w') as f: json.dump({"todos": todos}, f, indent=2)

    # Clear the main active todos file
    clear_active_todos()

def restore_stashed_todos() -> None:
    """Restore todos from the stashed backup file."""
    if not STASHED_TODOS_FILE.exists(): return

    try:
        with open(STASHED_TODOS_FILE, 'r') as f: data = json.load(f)
        todos = data.get("todos", [])
        if todos: store_active_todos(todos)
        STASHED_TODOS_FILE.unlink()
        return todos
    except (FileNotFoundError, json.JSONDecodeError): return None

def clear_stashed_todos() -> None:
    """Clear the stashed todos file."""
    if STASHED_TODOS_FILE.exists(): STASHED_TODOS_FILE.unlink()
##-##

#-#
