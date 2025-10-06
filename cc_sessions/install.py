#!/usr/bin/env python3
"""
CC-Sessions installer module for pip/pipx installation.
This module is imported and executed when running `cc-sessions` command.
"""

import sys
import os
import json
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    BOLD = '\033[1m'

def color(text, color_code):
    return f"{color_code}{text}{Colors.RESET}"

def get_package_root():
    """Get the root directory of the installed cc_sessions package."""
    return Path(__file__).parent

def get_project_root():
    """Get the root directory where cc-sessions should be installed."""
    return Path.cwd()

def main():
    SCRIPT_DIR = get_package_root()
    PROJECT_ROOT = get_project_root()

    print(color('\n╔════════════════════════════════════════════════════════════════╗', Colors.CYAN))
    print(color('║           CC-SESSIONS INSTALLER (Python Edition)              ║', Colors.CYAN))
    print(color('╚════════════════════════════════════════════════════════════════╝\n', Colors.CYAN))

    # Check if already installed
    sessions_dir = PROJECT_ROOT / 'sessions'
    if sessions_dir.exists():
        print(color('⚠️  cc-sessions appears to be already installed (sessions/ directory exists).', Colors.YELLOW))
        print(color('Update/reinstall logic will be available in a future version.', Colors.YELLOW))
        print(color('Exiting without changes.\n', Colors.YELLOW))
        sys.exit(0)

    print(color(f'Installing cc-sessions to: {PROJECT_ROOT}', Colors.CYAN))
    print()

    try:
        # Create directory structure
        create_directory_structure(PROJECT_ROOT)

        # Copy shared files
        copy_shared_files(SCRIPT_DIR, PROJECT_ROOT)

        # Copy Python-specific files
        copy_python_files(SCRIPT_DIR, PROJECT_ROOT)

        # Configure .claude/settings.json
        configure_settings(PROJECT_ROOT)

        # Add reference to CLAUDE.md
        configure_claude_md(PROJECT_ROOT)

        # Initialize state and config files
        initialize_state_files(PROJECT_ROOT)

        print(color('\n✅ cc-sessions installed successfully!\n', Colors.GREEN))
        print(color('Next steps:', Colors.BOLD))
        print('  1. Restart your Claude Code session (or run /clear)')
        print('  2. The kickstart onboarding will guide you through setup\n')

    except Exception as error:
        print(color(f'\n❌ Installation failed: {error}', Colors.RED), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_directory_structure(project_root):
    print(color('Creating directory structure...', Colors.CYAN))

    dirs = [
        '.claude',
        '.claude/agents',
        '.claude/commands',
        'sessions',
        'sessions/tasks',
        'sessions/tasks/done',
        'sessions/tasks/indexes',
        'sessions/hooks',
        'sessions/api',
        'sessions/protocols',
        'sessions/knowledge'
    ]

    for dir_name in dirs:
        full_path = project_root / dir_name
        full_path.mkdir(parents=True, exist_ok=True)

def copy_shared_files(script_dir, project_root):
    print(color('Installing shared files...', Colors.CYAN))

    # Copy agents
    agents_source = script_dir / 'agents'
    agents_dest = project_root / '.claude' / 'agents'
    if agents_source.exists():
        copy_directory(agents_source, agents_dest)

    # Copy knowledge base
    knowledge_source = script_dir / 'knowledge'
    knowledge_dest = project_root / 'sessions' / 'knowledge'
    if knowledge_source.exists():
        copy_directory(knowledge_source, knowledge_dest)

def copy_python_files(script_dir, project_root):
    print(color('Installing Python-specific files...', Colors.CYAN))

    py_root = script_dir / 'python'

    # Copy statusline
    copy_file(
        py_root / 'statusline.py',
        project_root / 'sessions' / 'statusline.py'
    )

    # Copy API
    copy_directory(
        py_root / 'api',
        project_root / 'sessions' / 'api'
    )

    # Copy hooks
    copy_directory(
        py_root / 'hooks',
        project_root / 'sessions' / 'hooks'
    )

    # Copy protocols
    copy_directory(
        py_root / 'protocols',
        project_root / 'sessions' / 'protocols'
    )

    # Copy commands
    copy_directory(
        py_root / 'commands',
        project_root / '.claude' / 'commands'
    )

    # Copy templates to their respective destinations
    templates_dir = py_root / 'templates'

    copy_file(
        templates_dir / 'CLAUDE.sessions.md',
        project_root / 'sessions' / 'CLAUDE.sessions.md'
    )

    copy_file(
        templates_dir / 'TEMPLATE.md',
        project_root / 'sessions' / 'tasks' / 'TEMPLATE.md'
    )

    copy_file(
        templates_dir / 'h-kickstart-setup.md',
        project_root / 'sessions' / 'tasks' / 'h-kickstart-setup.md'
    )

    copy_file(
        templates_dir / 'INDEX_TEMPLATE.md',
        project_root / 'sessions' / 'tasks' / 'indexes' / 'INDEX_TEMPLATE.md'
    )

def configure_settings(project_root):
    print(color('Configuring Claude Code hooks...', Colors.CYAN))

    settings_path = project_root / '.claude' / 'settings.json'
    settings = {}

    # Load existing settings if they exist
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print(color('⚠️  Could not parse existing settings.json, will create new one', Colors.YELLOW))

    # Define sessions hooks
    is_windows = sys.platform == 'win32'
    sessions_hooks = {
        'UserPromptSubmit': [
            {
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\user_messages.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/user_messages.py'
                    }
                ]
            }
        ],
        'PreToolUse': [
            {
                'matcher': 'Write|Edit|MultiEdit|Task|Bash',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\sessions_enforce.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/sessions_enforce.py'
                    }
                ]
            },
            {
                'matcher': 'Task',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\subagent_hooks.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/subagent_hooks.py'
                    }
                ]
            }
        ],
        'PostToolUse': [
            {
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\post_tool_use.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/post_tool_use.py'
                    }
                ]
            }
        ],
        'SessionStart': [
            {
                'matcher': 'startup|clear',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\session_start.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/session_start.py'
                    }
                ]
            }
        ]
    }

    # Initialize hooks object if it doesn't exist
    if 'hooks' not in settings:
        settings['hooks'] = {}

    # Merge each hook type (sessions hooks take precedence)
    for hook_type, hook_config in sessions_hooks.items():
        if hook_type not in settings['hooks']:
            settings['hooks'][hook_type] = []

        # Add sessions hooks (prepend so they run first)
        settings['hooks'][hook_type] = hook_config + settings['hooks'][hook_type]

    # Write updated settings
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)

def configure_claude_md(project_root):
    print(color('Configuring CLAUDE.md...', Colors.CYAN))

    claude_path = project_root / 'CLAUDE.md'
    reference = '@sessions/CLAUDE.sessions.md'

    if claude_path.exists():
        content = claude_path.read_text(encoding='utf-8')

        # Only add if not already present
        if reference not in content:
            # Add at the beginning after any frontmatter
            lines = content.split('\n')
            insert_index = 0

            # Skip frontmatter if it exists
            if lines[0] == '---':
                for i in range(1, len(lines)):
                    if lines[i] == '---':
                        insert_index = i + 1
                        break

            lines.insert(insert_index, '')
            lines.insert(insert_index + 1, reference)
            lines.insert(insert_index + 2, '')
            content = '\n'.join(lines)
            claude_path.write_text(content, encoding='utf-8')
    else:
        # Create minimal CLAUDE.md with reference
        minimal_claude = f"""# CLAUDE.md

{reference}

This file provides instructions for Claude Code when working with this codebase.
"""
        claude_path.write_text(minimal_claude, encoding='utf-8')

def initialize_state_files(project_root):
    print(color('Initializing state files...', Colors.CYAN))

    # Set environment variable so shared_state can find project root
    os.environ['CLAUDE_PROJECT_DIR'] = str(project_root)

    # Add sessions/hooks to path so we can import shared_state
    sys.path.insert(0, str(project_root / 'sessions' / 'hooks'))

    # Import and call load_state/load_config from shared_state
    try:
        from shared_state import load_state, load_config
    except ImportError as e:
        print(color('⚠️  Could not import shared_state module. File copying may have failed.', Colors.YELLOW))
        print(color(f'Error: {e}', Colors.YELLOW))
        sys.exit(1)

    # These functions create the files if they don't exist
    load_state()
    load_config()

    # Verify files were created
    state_file = project_root / 'sessions' / 'sessions-state.json'
    config_file = project_root / 'sessions' / 'sessions-config.json'

    if not state_file.exists() or not config_file.exists():
        print(color('⚠️  State files were not created properly', Colors.YELLOW))
        print(color('You may need to initialize them manually on first run', Colors.YELLOW))

# Utility functions

def copy_file(src, dest):
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

        # Preserve executable permissions
        try:
            src_mode = src.stat().st_mode
            dest.chmod(src_mode)
        except Exception:
            # Ignore chmod errors
            pass

def copy_directory(src, dest):
    if not src.exists():
        return

    dest.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        src_path = src / item.name
        dest_path = dest / item.name

        if item.is_dir():
            copy_directory(src_path, dest_path)
        else:
            copy_file(src_path, dest_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(color(f'\n❌ Fatal error: {error}', Colors.RED), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
