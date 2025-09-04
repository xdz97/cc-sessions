#!/usr/bin/env python3
"""Shared state management for Claude Code Sessions hooks."""
import json
from pathlib import Path
from datetime import datetime

# Get project root dynamically
def get_project_root():
    """Find project root by looking for .claude directory."""
    current = Path.cwd()
    while current.parent != current:
        if (current / ".claude").exists():
            return current
        current = current.parent
    # Fallback to current directory if no .claude found
    return Path.cwd()

PROJECT_ROOT = get_project_root()

# All state files in .claude/state/
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
DAIC_STATE_FILE = STATE_DIR / "daic-mode.json"
TASK_STATE_FILE = STATE_DIR / "current_task.json"

# Mode description strings
DISCUSSION_MODE_MSG = "You are now in Discussion Mode and should focus on discussing and investigating with the user (no edit-based tools)"
IMPLEMENTATION_MODE_MSG = "You are now in Implementation Mode and may use tools to execute the agreed upon actions - when you are done return immediately to Discussion Mode"

def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

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
    except (FileNotFoundError, json.JSONDecodeError):
        current_mode = "discussion"
    
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

# Task and branch state management

def parse_task_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from task file content."""
    if not content.startswith('---'):
        return {}
    
    lines = content.split('\n')
    frontmatter_lines = []
    in_frontmatter = False
    
    for i, line in enumerate(lines):
        if i == 0 and line == '---':
            in_frontmatter = True
            continue
        if in_frontmatter and line == '---':
            break
        if in_frontmatter:
            frontmatter_lines.append(line)
    
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
    
    return frontmatter

def update_task_frontmatter(file_path: Path, updates: dict) -> None:
    """Update frontmatter fields in a task file."""
    content = file_path.read_text()
    lines = content.split('\n')
    
    if not content.startswith('---'):
        return
    
    # Find frontmatter boundaries
    end_idx = 0
    for i, line in enumerate(lines[1:], 1):
        if line == '---':
            end_idx = i
            break
    
    # Update frontmatter lines
    for i in range(1, end_idx):
        for key, value in updates.items():
            if lines[i].startswith(f"{key}:"):
                if isinstance(value, list):
                    lines[i] = f"{key}: [{', '.join(value)}]"
                else:
                    lines[i] = f"{key}: {value}"
    
    # Write back
    file_path.write_text('\n'.join(lines))

def get_active_task_name() -> str:
    """Get the currently active task name from minimal current_task.json."""
    try:
        with open(TASK_STATE_FILE, 'r') as f:
            data = json.load(f)
            # Support both old format (full state) and new format (just task name)
            if isinstance(data, dict):
                return data.get("task", None)
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_task_state() -> dict:
    """Get current task state including branch and affected services.
    
    Reads task name from current_task.json, then loads full state from task file frontmatter.
    """
    # Get the active task name
    task_name = get_active_task_name()
    if not task_name:
        return {"task": None, "branch": None, "services": [], "updated": None}
    
    # Find the task file
    tasks_dir = PROJECT_ROOT / "sessions" / "tasks"
    task_file = tasks_dir / f"{task_name}.md"
    
    # Check if it's a directory task
    task_dir = tasks_dir / task_name
    if task_dir.is_dir():
        task_file = task_dir / "README.md"
    
    if not task_file.exists():
        # Task file not found, return just the name
        return {"task": task_name, "branch": None, "services": [], "updated": None}
    
    # Parse frontmatter
    content = task_file.read_text()
    frontmatter = parse_task_frontmatter(content)
    
    # Normalize to expected format (modules -> services)
    return {
        "task": task_name,
        "branch": frontmatter.get("branch", None),
        "services": frontmatter.get("modules", []),  # Map modules to services
        "updated": frontmatter.get("updated", frontmatter.get("created", None))
    }

def set_task_state(task: str, branch: str, services: list):
    """Set current task state.
    
    Updates both the current_task.json pointer and the task file frontmatter.
    """
    ensure_state_dir()
    
    # Update the pointer file (now minimal)
    with open(TASK_STATE_FILE, 'w') as f:
        json.dump({"task": task}, f, indent=2)
    
    # Update the task file frontmatter
    if task:
        tasks_dir = PROJECT_ROOT / "sessions" / "tasks"
        task_file = tasks_dir / f"{task}.md"
        
        # Check if it's a directory task
        task_dir = tasks_dir / task
        if task_dir.is_dir():
            task_file = task_dir / "README.md"
        
        if task_file.exists():
            updates = {
                "branch": branch,
                "modules": services,
                "updated": datetime.now().strftime("%Y-%m-%d")
            }
            update_task_frontmatter(task_file, updates)
    
    return {
        "task": task,
        "branch": branch,
        "services": services,
        "updated": datetime.now().strftime("%Y-%m-%d")
    }

def add_service_to_task(service: str):
    """Add a service to the current task's affected services list."""
    state = get_task_state()
    if service not in state.get("services", []):
        services = state.get("services", [])
        services.append(service)
        
        # Update using set_task_state to maintain consistency
        task_name = state.get("task")
        branch = state.get("branch")
        if task_name:
            return set_task_state(task_name, branch, services)
    return state

# Todo state management for DAIC enforcement
ACTIVE_TODOS_FILE = STATE_DIR / "active-todos.json"

def get_active_todos() -> list:
    """Get the currently active/approved todos."""
    try:
        with open(ACTIVE_TODOS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("todos", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def store_active_todos(todos: list) -> None:
    """Store the approved todo list as active execution scope."""
    ensure_state_dir()
    data = {"todos": todos}
    with open(ACTIVE_TODOS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def clear_active_todos() -> None:
    """Clear the active todos when returning to discussion mode."""
    if ACTIVE_TODOS_FILE.exists():
        ACTIVE_TODOS_FILE.unlink()

def check_todos_complete() -> bool:
    """Check if all todos in the active list are complete."""
    todos = get_active_todos()
    if not todos:
        return False
    
    # All todos must have status == 'completed'
    return all(t.get('status') == 'completed' for t in todos)