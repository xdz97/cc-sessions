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

FULL_MODE_SEQUENCE = [
    '03-core-workflow',
    '04-trigger-phrases',
    '05-orphaned-todos',
    '06-tasks-and-branches',
    '07-task-startup-and-config',
    '08-create-first-task',
    '09-always-available-protocols',
    '10-agent-customization',
    '11-code-review-customization',
    '12-tool-configuration',
    '13-advanced-features',
    '14-graduation'
]

API_MODE_SEQUENCE = [
    '03-core-workflow',
    '04-task-protocols',
    '05-context-management',
    '06-configuration',
    '07-agent-customization',
    '08-advanced-concepts',
    '09-create-first-task',
    '10-graduation'
]

SESHXPERT_SEQUENCE = [
    '03-quick-setup',
    '05-graduation'
]

#-#

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


def get_mode_sequence(mode: str) -> List[str]:
    """Get the module sequence for a given mode."""
    if mode == 'full':
        return FULL_MODE_SEQUENCE
    elif mode == 'api':
        return API_MODE_SEQUENCE
    elif mode == 'seshxpert':
        return SESHXPERT_SEQUENCE
    else:
        return []


def handle_kickstart_command(args: List[str], json_output: bool = False) -> Any:
    """
    Handle kickstart-specific commands for onboarding flow.

    Usage:
        kickstart next                  - Load next module chunk
        kickstart mode <mode>           - Initialize kickstart with selected mode
        kickstart remind <dd:hh>        - Set reminder date for "later" option
        kickstart complete              - Exit kickstart mode
    """
    if not args:
        return format_kickstart_help(json_output)

    command = args[0].lower()
    command_args = args[1:] if len(args) > 1 else []

    if command == 'next':
        return load_next_module(json_output)
    elif command == 'mode':
        if not command_args:
            error_msg = "Error: mode requires argument (full|api|seshxpert)"
            if json_output:
                return {"error": error_msg}
            return error_msg
        return set_kickstart_mode(command_args[0], json_output)
    elif command == 'remind':
        if not command_args:
            error_msg = "Error: remind requires dd:hh format (e.g., 1:00 for tomorrow)"
            if json_output:
                return {"error": error_msg}
            return error_msg
        return set_reminder(command_args[0], json_output)
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
        "mode <mode>": "Initialize kickstart with selected mode (full|api|seshxpert)",
        "remind <dd:hh>": "Set reminder date for 'later' option (e.g., 1:00 for tomorrow)",
        "complete": "Exit kickstart mode and clear noob flag"
    }

    if json_output:
        return {"available_commands": commands}

    lines = ["Kickstart Commands:"]
    for cmd, desc in commands.items():
        lines.append(f"  {cmd}: {desc}")
    return "\n".join(lines)


def load_next_module(json_output: bool = False) -> Any:
    """Load next module chunk based on current progress."""
    STATE = load_state()
    progress = STATE.metadata.get('kickstart_progress', {})

    if not progress:
        error_msg = "Error: No kickstart progress found. Start with 'mode' command first."
        if json_output:
            return {"error": error_msg}
        return error_msg

    mode = progress.get('mode', 'full')
    current = progress.get('current_module')

    # Get sequence for current mode
    sequence = get_mode_sequence(mode)

    if not sequence:
        error_msg = f"Error: Invalid mode '{mode}'"
        if json_output:
            return {"error": error_msg}
        return error_msg

    # Find next module
    try:
        current_idx = sequence.index(current)
        next_module = sequence[current_idx + 1]
    except IndexError:
        # Reached end of sequence
        return complete_kickstart(json_output)
    except ValueError:
        error_msg = f"Error: Current module '{current}' not found in sequence"
        if json_output:
            return {"error": error_msg}
        return error_msg

    # Update progress
    with edit_state() as s:
        s.metadata['kickstart_progress']['current_module'] = next_module
        if 'completed_modules' not in s.metadata['kickstart_progress']:
            s.metadata['kickstart_progress']['completed_modules'] = []
        s.metadata['kickstart_progress']['completed_modules'].append(current)
        s.metadata['kickstart_progress']['last_active'] = datetime.now().isoformat()

    # Load protocol content
    protocol_content = load_protocol_file(f'kickstart/{mode}/{next_module}.md')

    # Format with config if needed
    if '{config}' in protocol_content:
        config = load_config()
        config_display = format_config_for_display(config)
        protocol_content = protocol_content.format(config=config_display)

    if json_output:
        return {
            "success": True,
            "mode": mode,
            "next_module": next_module,
            "protocol": protocol_content
        }

    return protocol_content


def set_kickstart_mode(mode_str: str, json_output: bool = False) -> Any:
    """Initialize kickstart with selected mode."""
    mode_str = mode_str.lower()

    if mode_str not in ['full', 'api', 'seshxpert']:
        error_msg = f"Error: Invalid mode '{mode_str}'. Use: full, api, or seshxpert"
        if json_output:
            return {"error": error_msg}
        return error_msg

    sequence = get_mode_sequence(mode_str)
    first_module = sequence[0]

    with edit_state() as s:
        s.metadata['kickstart_progress'] = {
            'mode': mode_str,
            'started': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'current_module': first_module,
            'completed_modules': [],
            'agent_progress': {}
        }

    # Load first module for selected mode
    protocol_content = load_protocol_file(f'kickstart/{mode_str}/{first_module}.md')

    # Format with config if needed
    if '{config}' in protocol_content:
        config = load_config()
        config_display = format_config_for_display(config)
        protocol_content = protocol_content.format(config=config_display)

    if json_output:
        return {
            "success": True,
            "mode": mode_str,
            "first_module": first_module,
            "protocol": protocol_content
        }

    return protocol_content


def set_reminder(date_str: str, json_output: bool = False) -> Any:
    """Set reminder date for 'later' option."""
    # Parse dd:hh format
    try:
        days, hours = date_str.split(':')
        days, hours = int(days), int(hours)
    except ValueError:
        error_msg = f"Error: Invalid format '{date_str}'. Use dd:hh (e.g., 1:00 for tomorrow)"
        if json_output:
            return {"error": error_msg}
        return error_msg

    reminder_time = datetime.now() + timedelta(days=days, hours=hours)

    with edit_state() as s:
        s.metadata['kickstart_reminder_date'] = reminder_time.isoformat()

    formatted_time = reminder_time.strftime('%Y-%m-%d %H:%M')

    if json_output:
        return {
            "success": True,
            "reminder_date": reminder_time.isoformat(),
            "formatted": formatted_time
        }

    return f"Reminder set for {formatted_time}. I'll ask about kickstart again then."


def complete_kickstart(json_output: bool = False) -> Any:
    """Exit kickstart mode, clean up files, and return cleanup instructions."""
    STATE = load_state()

    # Get install language (default to 'py' if not set)
    install_lang = STATE.metadata.get('install_lang', 'py')

    # Switch to implementation mode if in discussion mode
    if STATE.mode == Mode.NO:
        with edit_state() as s:
            s.mode = Mode.GO

    # Delete kickstart files immediately
    sessions_dir = PROJECT_ROOT / 'sessions'

    # 1. Delete kickstart hook (language-specific)
    if install_lang == 'py':
        hook_file = sessions_dir / 'hooks' / 'kickstart_session_start.py'
    else:  # 'js'
        hook_file = sessions_dir / 'hooks' / 'kickstart_session_start.js'

    if hook_file.exists():
        hook_file.unlink()

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

    # 4. Clear noob flag and kickstart metadata
    with edit_state() as s:
        s.flags.noob = False
        s.metadata.pop('kickstart_progress', None)
        s.metadata.pop('kickstart_reminder_date', None)

    # Generate language-specific cleanup instructions
    if install_lang == 'py':
        instructions = """Kickstart complete! The noob flag has been cleared.

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/scripts/api/router.py
□ Remove 'kickstart': handle_kickstart_command from COMMAND_HANDLERS in router.py
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/scripts/api/kickstart_commands.py

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install."""
    else:  # 'js'
        instructions = """Kickstart complete! The noob flag has been cleared.

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/scripts/api/router.js
□ Remove 'kickstart': handleKickstartCommand from COMMAND_HANDLERS in router.js
□ Remove kickstart SessionStart hook entry from .claude/settings.json.js
□ Delete sessions/scripts/api/kickstart_commands.js

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install."""

    if json_output:
        return {
            "success": True,
            "install_lang": install_lang,
            "instructions": instructions
        }

    return instructions

#-#
