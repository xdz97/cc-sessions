#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from typing import Any, List, Optional, Dict
import json
from importlib.metadata import version, PackageNotFoundError
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from hooks.shared_state import load_state, edit_state, Mode
##-##

#-#

# ===== GLOBALS ===== #
#-#

# ===== DECLARATIONS ===== #
#-#

# ===== CLASSES ===== #
#-#

# ===== FUNCTIONS ===== #

#!> State inspection handlers
def handle_state_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle state inspection commands.
    
    Usage:
        state [component] [--json]
        state task.name [--json]
        state todos.active [--json]
    """
    state = load_state()
    
    if not args:
        # Return full state
        if json_output:
            return state.to_dict()
        else:
            return format_state_human(state)
    
    component = args[0]
    
    # Handle nested access (e.g., task.name, flags.noob)
    if '.' in component:
        parts = component.split('.')
        result = state.to_dict()
        try:
            for part in parts:
                if isinstance(result, dict):
                    result = result.get(part)
                elif hasattr(result, part):
                    result = getattr(result, part)
                else:
                    raise ValueError(f"Invalid state path: {component}")
            
            if json_output:
                return {component: result}
            else:
                return f"{component}: {result}"
        except (KeyError, AttributeError):
            raise ValueError(f"Invalid state path: {component}")
    
    # Handle top-level components
    if component == 'mode':
        if json_output:
            return {"mode": state.mode.value}
        return f"Mode: {state.mode.value}"
    
    elif component == 'task':
        if json_output:
            return {"task": state.current_task.task_state if state.current_task else None}
        if state.current_task:
            return format_task_human(state.current_task)
        return "No active task"
    
    elif component == 'todos':
        if json_output:
            return {"todos": state.todos.to_dict()}
        return format_todos_human(state.todos)
    
    elif component == 'flags':
        if json_output:
            return {"flags": state.flags.to_dict()}
        return format_flags_human(state.flags)
    
    elif component == 'metadata':
        if json_output:
            return {"metadata": state.metadata}
        return f"Metadata: {json.dumps(state.metadata, indent=2)}"
    
    else:
        raise ValueError(f"Unknown state component: {component}")

def format_state_human(state) -> str:
    """Format full state for human reading."""
    lines = [
        "=== Session State ===",
        f"Mode: {state.mode.value}",
        "",
    ]
    
    if state.current_task:
        lines.append("Current Task:")
        lines.append(f"  Name: {state.current_task.name}")
        lines.append(f"  File: {state.current_task.file}")
        lines.append(f"  Branch: {state.current_task.branch}")
        lines.append(f"  Status: {state.current_task.status}")
    else:
        lines.append("Current Task: None")
    
    lines.append("")
    lines.append(f"Active Todos: {len(state.todos.active)}")
    for i, todo in enumerate(state.todos.active):
        status_icon = "✓" if todo.get('status') == 'completed' else "○"
        lines.append(f"  {status_icon} {todo.get('content', 'Unknown')}")
    
    if state.todos.stashed:
        lines.append(f"Stashed Todos: {len(state.todos.stashed)}")
    
    lines.append("")
    lines.append("Flags:")
    lines.append(f"  Context 85% warning: {state.flags.context_85}")
    lines.append(f"  Context 90% warning: {state.flags.context_90}")
    lines.append(f"  Subagent mode: {state.flags.subagent}")
    lines.append(f"  Noob mode: {state.flags.noob}")
    lines.append(f"  Bypass mode: {state.flags.bypass_mode}")
    
    return "\n".join(lines)

def format_task_human(task) -> str:
    """Format task for human reading."""
    lines = ["Current Task:"]
    if task.name:
        lines.append(f"  Name: {task.name}")
    if task.file:
        lines.append(f"  File: {task.file}")
    if task.branch:
        lines.append(f"  Branch: {task.branch}")
    if task.status:
        lines.append(f"  Status: {task.status}")
    if task.created:
        lines.append(f"  Created: {task.created}")
    if task.started:
        lines.append(f"  Started: {task.started}")
    if task.submodules:
        lines.append(f"  Submodules: {', '.join(task.submodules)}")
    return "\n".join(lines)

def format_todos_human(todos) -> str:
    """Format todos for human reading."""
    lines = []
    
    if todos.active:
        lines.append(f"Active Todos ({len(todos.active)}):")
        for i, todo in enumerate(todos.active, 1):
            status = todo.get('status', 'pending')
            icon = {"completed": "✓", "in_progress": "→", "pending": "○"}.get(status, "?")
            lines.append(f"  {i}. [{icon}] {todo.get('content', 'Unknown')}")
    else:
        lines.append("Active Todos: None")
    
    if todos.stashed:
        lines.append(f"\nStashed Todos ({len(todos.stashed)}):")
        for i, todo in enumerate(todos.stashed, 1):
            lines.append(f"  {i}. {todo.get('content', 'Unknown')}")
    
    return "\n".join(lines)

def format_flags_human(flags) -> str:
    """Format flags for human reading."""
    lines = ["Flags:"]
    lines.append(f"  context_85: {flags.context_85}")
    lines.append(f"  context_90: {flags.context_90}")
    lines.append(f"  subagent: {flags.subagent}")
    lines.append(f"  noob: {flags.noob}")
    lines.append(f"  bypass_mode: {flags.bypass_mode}")
    return "\n".join(lines)
#!<

#!> Mode command handler
def handle_mode_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle mode switching commands.

    Usage:
        mode discussion  - Switch to discussion mode (one-way only)
        mode bypass      - Toggle bypass mode (disables behavioral constraints)
    """
    if not args:
        # Just show current mode and bypass status
        state = load_state()
        if json_output:
            return {"mode": state.mode.value, "bypass_mode": state.flags.bypass_mode}
        result = f"Current mode: {state.mode.value}"
        if state.flags.bypass_mode:
            result += "\nBypass mode: ACTIVE (behavioral constraints disabled)"
        return result

    target_mode = args[0].lower()

    if target_mode == 'discussion':
        # One-way switch to discussion allowed
        with edit_state() as state:
            if state.mode == Mode.GO:
                state.mode = Mode.NO
                if json_output:
                    return {"mode": "discussion", "message": "Switched to discussion mode"}
                return "Switched to discussion mode"
            else:
                if json_output:
                    return {"mode": "discussion", "message": "Already in discussion mode"}
                return "Already in discussion mode"

    elif target_mode == 'bypass':
        # Check if this is a slash command (user-initiated) or API call (Claude-initiated)
        is_slash_command = '--from-slash' in args

        with edit_state() as state:
            if state.flags.bypass_mode:
                # Always allow deactivating bypass mode (returning to safety)
                state.flags.bypass_mode = False
                if json_output:
                    return {"bypass_mode": False, "message": "Bypass mode INACTIVE"}
                return "Bypass mode INACTIVE - behavioral constraints enabled"
            else:
                # Only allow activating bypass if it's from a slash command (user-initiated)
                if not is_slash_command:
                    raise ValueError("Cannot activate bypass mode via API. Only the user can enable bypass mode.")
                state.flags.bypass_mode = True
                if json_output:
                    return {"bypass_mode": True, "message": "Bypass mode ACTIVE"}
                return "Bypass mode ACTIVE - behavioral constraints disabled"

    elif target_mode == 'implementation':
        # Not allowed via API
        raise ValueError("Cannot switch to implementation mode via API. Use trigger phrases instead.")

    else:
        raise ValueError(f"Unknown mode: {target_mode}. Valid modes: discussion, bypass")
#!<

#!> Flags command handler
def handle_flags_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle flag management commands.
    
    Usage:
        flags clear         - Clear all flags
        flags clear-context - Clear context warnings only
    """
    if not args:
        # Show current flags
        state = load_state()
        if json_output:
            return {"flags": state.flags.to_dict()}
        return format_flags_human(state.flags)
    
    action = args[0].lower()
    
    if action == 'clear':
        with edit_state() as state:
            state.flags.context_85 = False
            state.flags.context_90 = False
            state.flags.subagent = False
            state.flags.noob = False
        
        if json_output:
            return {"message": "All flags cleared"}
        return "All flags cleared"
    
    elif action == 'clear-context':
        with edit_state() as state:
            state.flags.context_85 = False
            state.flags.context_90 = False
        
        if json_output:
            return {"message": "Context warnings cleared"}
        return "Context warnings cleared"
    
    else:
        raise ValueError(f"Unknown flags action: {action}. Valid actions: clear, clear-context")
#!<

#!> Todos handler
def handle_todos_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle todos management commands.

    Usage:
        todos clear - Clear all active todos (requires api.todos_clear permission for API, always available via slash command)
    """
    if not args:
        # Show current todos
        state = load_state()
        if json_output:
            return {"todos": state.todos.to_dict()}
        lines = ["Active Todos:"]
        for todo in state.todos.active:
            status = todo.get('status', 'pending')
            content = todo.get('content', 'Unknown')
            lines.append(f"  [{status}] {content}")
        if not state.todos.active:
            lines.append("  (none)")
        return "\n".join(lines)

    # Check if --from-slash flag is present
    is_slash_command = '--from-slash' in args
    if is_slash_command:
        args = [arg for arg in args if arg != '--from-slash']

    if not args:
        raise ValueError("todos command requires an action. Valid actions: clear")

    action = args[0].lower()

    if action == 'clear':
        # Check if we have permission (only for API calls, not slash commands)
        state = load_state()
        if not is_slash_command and not state.api.todos_clear:
            if json_output:
                return {"error": "Permission denied: todos clear command is not available in this context"}
            return "Permission denied: The todos clear command is only available immediately after todos are restored"

        # Clear the todos
        with edit_state() as state:
            state.todos.clear_active()
            # Only disable permission if this was an API call
            if not is_slash_command and state.api.todos_clear:
                state.api.todos_clear = False

        if json_output:
            return {"message": "Active todos cleared"}
        return "Active todos cleared"

    else:
        raise ValueError(f"Unknown todos action: {action}. Valid actions: clear")
#!<

#!> Status and version handlers
def handle_status_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle status command - human-readable summary of current state.
    """
    state = load_state()
    
    if json_output:
        # For JSON, just return the full state
        return state.to_dict()
    
    # Human-readable status summary
    lines = [
        "╔══════════════════════════════════════╗",
        "║      CC-Sessions Status Summary      ║",
        "╚══════════════════════════════════════╝",
        "",
        f"Mode: {state.mode.value.upper()}",
    ]
    
    if state.current_task and state.current_task.name:
        lines.append(f"Task: {state.current_task.name} ({state.current_task.status or 'unknown'})")
    else:
        lines.append("Task: None")
    
    active_count = len(state.todos.active) if state.todos.active else 0
    completed = sum(1 for t in state.todos.active if t.get('status') == 'completed') if state.todos.active else 0
    lines.append(f"Todos: {completed}/{active_count} completed")
    
    # Warnings
    warnings = []
    if state.flags.context_85:
        warnings.append("85% context usage")
    if state.flags.context_90:
        warnings.append("90% context usage")
    if warnings:
        lines.append(f"⚠ Warnings: {', '.join(warnings)}")
    
    return "\n".join(lines)

def handle_version_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle version command - show package version.
    """
    try:
        pkg_version = version("cc-sessions")
    except PackageNotFoundError:
        pkg_version = "development"
    
    if json_output:
        return {"version": pkg_version}
    return f"cc-sessions version: {pkg_version}"
#!<

#-#