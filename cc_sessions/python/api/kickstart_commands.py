#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from typing import Any, List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
import shutil
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
from hooks.shared_state import load_state, edit_state, load_config, PROJECT_ROOT, Mode
##-##

#-#

# ===== GLOBALS ===== #

CONFIG = load_config()
STATE = load_state()

#-#

"""
╔═══════════════════════════════════════════════════════════════════════════╗
║     ██╗██╗  ██╗██████╗ █████╗██╗  ██╗██████╗██████╗ █████╗ █████╗ ██████╗ ║
║    ██╔╝██║ ██╔╝╚═██╔═╝██╔═══╝██║ ██╔╝██╔═══╝╚═██╔═╝██╔══██╗██╔═██╗╚═██╔═╝ ║
║   ██╔╝ █████╔╝   ██║  ██║    █████╔╝ ██████╗  ██║  ███████║█████╔╝  ██║   ║
║  ██╔╝  ██╔═██╗   ██║  ██║    ██╔═██╗ ╚═══██║  ██║  ██╔══██║██╔═██╗  ██║   ║
║ ██╔╝   ██║  ██╗██████╗╚█████╗██║  ██╗██████║  ██║  ██║  ██║██║ ██║  ██║   ║
║ ╚═╝    ╚═╝  ╚═╝╚═════╝ ╚════╝╚═╝  ╚═╝╚═════╝  ╚═╝  ╚═╝  ╚═╝╚═╝ ╚═╝  ╚═╝   ║
╚═══════════════════════════════════════════════════════════════════════════╝
Kickstart API handlers
"""


# ===== FUNCTIONS ===== #

def format_config_for_display(config) -> str:
    """Format config as readable markdown for kickstart display."""
    return f"""**Current Configuration:**

**Trigger Phrases:**
- Implementation mode: {config.trigger_phrases.implementation_mode}
- Discussion mode: {config.trigger_phrases.discussion_mode}
- Task creation: {config.trigger_phrases.task_creation}
- Task startup: {config.trigger_phrases.task_startup}
- Task completion: {config.trigger_phrases.task_completion}
- Context compaction: {config.trigger_phrases.context_compaction}

**Git Preferences:**
- Default branch: {config.git_preferences.default_branch}
- Has submodules: {config.git_preferences.has_submodules}
- Add pattern: {config.git_preferences.add_pattern}

**Environment:**
- Developer name: {config.environment.developer_name}
- Project root: {config.environment.project_root}"""


def load_protocol_file(relative_path: str) -> str:
    """Load protocol markdown from protocols directory."""
    protocol_path = PROJECT_ROOT / 'sessions' / 'protocols' / relative_path
    if not protocol_path.exists():
        return f"Error: Protocol file not found: {relative_path}"
    return protocol_path.read_text()


def handle_kickstart_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle kickstart-specific commands for onboarding flow.

    Usage:
        kickstart next      - Load next module chunk
        kickstart complete  - Exit kickstart mode
    """
    if not args:
        return format_kickstart_help(json_output)

    command = args[0].lower()
    command_args = args[1:] if len(args) > 1 else []

    if command == 'next':
        return load_next_module(json_output)
    elif command == 'complete':
        return complete_kickstart(json_output)
    else:
        error_msg = f"Unknown kickstart command: {command}"
        if json_output:
            return {"error": error_msg}
        return error_msg


def format_kickstart_help(json_output: bool) -> Any:
    """Format help for kickstart commands."""
    commands = {
        "next": "Load next module chunk based on current progress",
        "complete": "Exit kickstart mode and clean up files"
    }

    if json_output:
        return {"available_commands": commands}

    lines = ["Kickstart Commands:"]
    for cmd, desc in commands.items():
        lines.append(f"  {cmd}: {desc}")
    return "\n".join(lines)


def load_next_module(json_output: bool = False) -> Any:
    """Load next module chunk based on current progress."""
    kickstart_meta = STATE.metadata.get('kickstart')

    if not kickstart_meta:
        error_msg = "Error: No kickstart metadata found. This is a bug."
        if json_output:
            return {"error": error_msg}
        return error_msg

    sequence = kickstart_meta.get('sequence')
    current_index = kickstart_meta.get('current_index')
    completed = kickstart_meta.get('completed', [])

    if not sequence:
        error_msg = "Error: No kickstart sequence found. This is a bug."
        if json_output:
            return {"error": error_msg}
        return error_msg

    # Mark current as completed
    current_file = sequence[current_index]

    # Move to next
    next_index = current_index + 1

    # Check if we've reached the end
    if next_index >= len(sequence):
        return complete_kickstart(json_output)

    next_file = sequence[next_index]

    # Update state
    with edit_state() as s:
        s.metadata['kickstart']['current_index'] = next_index
        s.metadata['kickstart']['completed'].append(current_file)
        s.metadata['kickstart']['last_active'] = datetime.now().isoformat()

    # Load next protocol
    protocol_content = load_protocol_file(f'kickstart/{next_file}')

    if json_output:
        return {
            "success": True,
            "next_file": next_file,
            "protocol": protocol_content
        }

    return protocol_content


def complete_kickstart(json_output: bool = False) -> Any:
    """Exit kickstart mode, clean up files, and return cleanup instructions."""
    # Switch to implementation mode if in discussion mode
    if STATE.mode == Mode.NO:
        with edit_state() as s:
            s.mode = Mode.GO

    # Delete kickstart files immediately
    sessions_dir = PROJECT_ROOT / 'sessions'

    # 1. Delete kickstart hook (check both language variants)
    py_hook = sessions_dir / 'hooks' / 'kickstart_session_start.py'
    js_hook = sessions_dir / 'hooks' / 'kickstart_session_start.js'

    if py_hook.exists():
        py_hook.unlink()
        is_python = True
    elif js_hook.exists():
        js_hook.unlink()
        is_python = False
    else:
        is_python = True  # default fallback

    # 2. Delete kickstart protocols directory
    protocols_dir = sessions_dir / 'protocols' / 'kickstart'
    if protocols_dir.exists():
        shutil.rmtree(protocols_dir)

    # 3. Delete kickstart setup task (check both locations)
    task_file = sessions_dir / 'tasks' / 'h-kickstart-setup.md'
    if not task_file.exists():
        task_file = sessions_dir / 'tasks' / 'done' / 'h-kickstart-setup.md'

    if task_file.exists():
        task_file.unlink()

    # 4. Clear kickstart metadata
    with edit_state() as s:
        s.metadata.pop('kickstart', None)

    # Generate language-specific cleanup instructions based on which hook was found
    if is_python:
        instructions = """Kickstart complete!

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/api/router.py
□ Remove 'kickstart': handle_kickstart_command from COMMAND_HANDLERS in router.py
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/api/kickstart_commands.py

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install."""
    else:  # JavaScript
        instructions = """Kickstart complete!

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/api/router.js
□ Remove 'kickstart': handleKickstartCommand from COMMAND_HANDLERS in router.js
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/api/kickstart_commands.js

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install."""

    if json_output:
        return {
            "success": True,
            "instructions": instructions
        }

    return instructions

#-#
