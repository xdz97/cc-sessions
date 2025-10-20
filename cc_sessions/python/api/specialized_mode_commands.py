#!/usr/bin/env python3
"""
Specialized Mode Commands - API commands for managing specialized modes
"""
import sys
import json
from pathlib import Path
from typing import List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cc_sessions.python.hooks.shared_state import (
    load_state, save_state, SpecializedMode, SPECIALIZED_MODE_CONFIGS,
    Mode, IconStyle, get_config
)


def cmd_list_modes(args: List[str], json_output: bool = False) -> None:
    """List all available specialized modes with descriptions."""
    CONFIG = get_config()
    icon_style = CONFIG.features.icon_style

    if json_output:
        modes_data = {}
        for mode in SpecializedMode:
            if mode == SpecializedMode.NONE:
                continue
            config = SPECIALIZED_MODE_CONFIGS.get(mode)
            if config:
                modes_data[mode.value] = {
                    "name": config.name,
                    "description": config.description,
                    "allowed_tools": [t.value for t in config.allowed_tools],
                    "blocked_tools": [t.value for t in config.blocked_tools],
                    "exit_phrases": config.exit_phrases,
                    "protocol_file": config.protocol_file
                }
        print(json.dumps(modes_data, indent=2))
        return

    # Emoji output
    if icon_style == IconStyle.NERD_FONTS:
        mode_icon = "󰒓"  # nf-md-cog
        tool_icon = "󰢴"   # nf-md-tools
    elif icon_style == IconStyle.EMOJI:
        mode_icon = "⚙️"
        tool_icon = "🔧"
    else:  # ASCII
        mode_icon = "[M]"
        tool_icon = "[T]"

    print(f"\n{mode_icon} Available Specialized Modes:\n")

    for mode in SpecializedMode:
        if mode == SpecializedMode.NONE:
            continue

        config = SPECIALIZED_MODE_CONFIGS.get(mode)
        if config:
            print(f"  {mode.value}")
            print(f"    Description: {config.description}")
            print(f"    Trigger: /sessions mode {mode.value} <args>")
            print(f"    {tool_icon} Allowed: {', '.join([t.value for t in config.allowed_tools])}")
            if config.blocked_tools:
                print(f"    {tool_icon} Blocked: {', '.join([t.value for t in config.blocked_tools])}")
            print(f"    Exit phrases: {', '.join(config.exit_phrases[:3])}...")
            print()


def cmd_enter_mode(args: List[str], json_output: bool = False) -> None:
    """Enter a specialized mode with optional arguments."""
    if not args:
        print("Error: No mode specified. Use: sessions mode <mode_name> [args...]", file=sys.stderr)
        sys.exit(1)

    mode_name = args[0]
    mode_args = args[1:] if len(args) > 1 else []

    # Validate mode
    try:
        mode = SpecializedMode(mode_name)
    except ValueError:
        print(f"Error: Invalid mode '{mode_name}'. Use 'sessions mode list' to see available modes.", file=sys.stderr)
        sys.exit(1)

    if mode == SpecializedMode.NONE:
        print("Error: Cannot explicitly enter NONE mode. Use 'sessions mode exit' to exit current mode.", file=sys.stderr)
        sys.exit(1)

    # Get mode config
    config = SPECIALIZED_MODE_CONFIGS.get(mode)
    if not config:
        print(f"Error: No configuration found for mode '{mode_name}'.", file=sys.stderr)
        sys.exit(1)

    # Update state
    STATE = load_state()
    STATE.specialized_mode = mode

    # Store mode arguments in metadata if provided
    if mode_args:
        if 'specialized_mode_args' not in STATE.metadata:
            STATE.metadata['specialized_mode_args'] = {}
        STATE.metadata['specialized_mode_args'][mode.value] = mode_args

    save_state(STATE)

    if json_output:
        result = {
            "mode": mode.value,
            "arguments": mode_args,
            "config": {
                "description": config.description,
                "allowed_tools": [t.value for t in config.allowed_tools],
                "blocked_tools": [t.value for t in config.blocked_tools],
            }
        }
        print(json.dumps(result, indent=2))
        return

    CONFIG = get_config()
    icon_style = CONFIG.features.icon_style

    if icon_style == IconStyle.NERD_FONTS:
        mode_icon = "󰒓"  # nf-md-cog
    elif icon_style == IconStyle.EMOJI:
        mode_icon = "⚙️"
    else:  # ASCII
        mode_icon = "[M]"

    print(f"\n{mode_icon} Entered {mode.value} mode")
    print(f"  Description: {config.description}")
    if mode_args:
        print(f"  Arguments: {' '.join(mode_args)}")
    print(f"\n  To exit this mode, use one of these phrases:")
    for phrase in config.exit_phrases:
        print(f"    - \"{phrase}\"")
    print()


def cmd_exit_mode(args: List[str], json_output: bool = False) -> None:
    """Exit the current specialized mode and return to normal mode."""
    STATE = load_state()

    previous_mode = STATE.specialized_mode
    if previous_mode == SpecializedMode.NONE:
        if not json_output:
            print("Not currently in a specialized mode.")
        return

    STATE.specialized_mode = SpecializedMode.NONE

    # Clear mode arguments from metadata
    if 'specialized_mode_args' in STATE.metadata:
        STATE.metadata['specialized_mode_args'].pop(previous_mode.value, None)

    save_state(STATE)

    if json_output:
        result = {
            "exited_mode": previous_mode.value,
            "current_mode": "none"
        }
        print(json.dumps(result, indent=2))
        return

    CONFIG = get_config()
    icon_style = CONFIG.features.icon_style

    if icon_style == IconStyle.NERD_FONTS:
        mode_icon = "󰒓"  # nf-md-cog
    elif icon_style == IconStyle.EMOJI:
        mode_icon = "⚙️"
    else:  # ASCII
        mode_icon = "[M]"

    print(f"\n{mode_icon} Exited {previous_mode.value} mode")
    print("  Returned to normal mode.")
    print()


def cmd_current_mode(args: List[str], json_output: bool = False) -> None:
    """Show the current specialized mode."""
    STATE = load_state()
    CONFIG = get_config()
    icon_style = CONFIG.features.icon_style

    current_mode = STATE.specialized_mode
    mode_args = STATE.metadata.get('specialized_mode_args', {}).get(current_mode.value, [])

    if json_output:
        result = {
            "mode": current_mode.value,
            "arguments": mode_args
        }
        if current_mode != SpecializedMode.NONE:
            config = SPECIALIZED_MODE_CONFIGS.get(current_mode)
            if config:
                result["config"] = {
                    "description": config.description,
                    "allowed_tools": [t.value for t in config.allowed_tools],
                    "blocked_tools": [t.value for t in config.blocked_tools],
                }
        print(json.dumps(result, indent=2))
        return

    if icon_style == IconStyle.NERD_FONTS:
        mode_icon = "󰒓"  # nf-md-cog
    elif icon_style == IconStyle.EMOJI:
        mode_icon = "⚙️"
    else:  # ASCII
        mode_icon = "[M]"

    if current_mode == SpecializedMode.NONE:
        print(f"\n{mode_icon} Current Mode: Normal (no specialized mode)")
        print()
        return

    config = SPECIALIZED_MODE_CONFIGS.get(current_mode)
    print(f"\n{mode_icon} Current Mode: {current_mode.value}")
    if config:
        print(f"  Description: {config.description}")
    if mode_args:
        print(f"  Arguments: {' '.join(mode_args)}")
    print()


def route_specialized_mode_command(subcmd: str, args: List[str], json_output: bool = False) -> None:
    """Route specialized mode subcommands to appropriate handlers."""
    handlers = {
        'list': cmd_list_modes,
        'enter': cmd_enter_mode,
        'exit': cmd_exit_mode,
        'current': cmd_current_mode,
    }

    handler = handlers.get(subcmd)
    if not handler:
        print(f"Unknown specialized mode command: {subcmd}", file=sys.stderr)
        print("Available commands: list, enter, exit, current", file=sys.stderr)
        sys.exit(1)

    handler(args, json_output)
