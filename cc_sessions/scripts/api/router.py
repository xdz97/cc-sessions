#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from typing import Any, List, Optional, Dict
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from api.state_commands import handle_state_command, handle_mode_command, handle_flags_command, handle_status_command, handle_version_command, handle_todos_command
from api.config_commands import handle_config_command
from api.protocol_commands import handle_protocol_command
from api.task_commands import handle_task_command
from api.kickstart_commands import handle_kickstart_command
##-##

#-#

# ===== GLOBALS ===== #

COMMAND_HANDLERS = {
    'protocol': handle_protocol_command,
    'state': handle_state_command,
    'mode': handle_mode_command,
    'flags': handle_flags_command,
    'status': handle_status_command,
    'version': handle_version_command,
    'config': handle_config_command,
    'todos': handle_todos_command,
    'tasks': handle_task_command,
    'kickstart': handle_kickstart_command,
}

#-#

# ===== DECLARATIONS ===== #
#-#

# ===== CLASSES ===== #
#-#

# ===== FUNCTIONS ===== #

def route_command(command: str, args: List[str], json_output: bool = False, from_slash: bool = False) -> Any:
    """
    Route a command to the appropriate handler.

    Args:
        command: Main command to execute
        args: Additional arguments for the command
        json_output: Whether to format output as JSON
        from_slash: Whether the command came from a slash command

    Returns:
        Command result (dict for JSON, string for human-readable)

    Raises:
        ValueError: If command is unknown or invalid
    """
    # Special handling for slash command router
    if command == 'slash':
        if not args:
            return format_slash_help()

        subsystem = args[0].lower()
        subsystem_args = args[1:] if len(args) > 1 else []

        # Route to appropriate subsystem
        if subsystem in ['tasks', 'state', 'config']:
            return route_command(subsystem, subsystem_args, json_output=json_output, from_slash=True)
        elif subsystem == 'help':
            return format_slash_help()
        else:
            return f"Unknown subsystem: {subsystem}\n\nValid subsystems: tasks, state, config\n\nUse '/sessions help' for full usage information."

    if command not in COMMAND_HANDLERS:
        raise ValueError(f"Unknown command: {command}. Available commands: {', '.join(COMMAND_HANDLERS.keys())}")

    handler = COMMAND_HANDLERS[command]

    # Pass from_slash to commands that support it
    if command in ['config', 'state', 'tasks']:
        return handler(args, json_output=json_output, from_slash=from_slash)
    else:
        # For commands that don't support from_slash, add it to args for backward compatibility
        if from_slash and '--from-slash' not in args:
            args = args + ['--from-slash']
        return handler(args, json_output=json_output)

def format_slash_help() -> str:
    """Format help output for unified /sessions slash command."""
    lines = [
        "# /sessions - Unified Sessions Management",
        "",
        "Manage all aspects of your Claude Code session from one command.",
        "",
        "## Available Subsystems",
        "",
        "### Tasks",
        "  /sessions tasks idx list        - List all task indexes",
        "  /sessions tasks idx <name>      - Show pending tasks in index",
        "  /sessions tasks start @<name>   - Start working on a task",
        "",
        "### State",
        "  /sessions state                 - Display current state",
        "  /sessions state show [section]  - Show specific section (task, todos, flags, mode)",
        "  /sessions state mode <mode>     - Switch mode (discussion/no, bypass/off)",
        "  /sessions state task <action>   - Manage task (clear, show, restore <file>)",
        "  /sessions state todos <action>  - Manage todos (clear)",
        "  /sessions state flags <action>  - Manage flags (clear, clear-context)",
        "",
        "### Config",
        "  /sessions config show           - Display current configuration",
        "  /sessions config trigger ...    - Manage trigger phrases",
        "  /sessions config git ...        - Manage git preferences",
        "  /sessions config env ...        - Manage environment settings",
        "  /sessions config readonly ...   - Manage readonly bash commands",
        "  /sessions config features ...   - Manage feature toggles",
        "",
        "## Quick Reference",
        "",
        "**Common Operations:**",
        "  /sessions tasks idx list                    # Browse available tasks",
        "  /sessions tasks start @my-task              # Start a task",
        "  /sessions state show task                   # Check current task",
        "  /sessions state mode no                     # Switch to discussion mode",
        "  /sessions config show                       # View all settings",
        "",
        "**Use '/sessions <subsystem> help' for detailed help on each subsystem**",
    ]
    return "\n".join(lines)

#-#
