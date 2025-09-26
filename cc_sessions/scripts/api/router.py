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
}

#-#

# ===== DECLARATIONS ===== #
#-#

# ===== CLASSES ===== #
#-#

# ===== FUNCTIONS ===== #

def route_command(command: str, args: List[str], json_output: bool = False) -> Any:
    """
    Route a command to the appropriate handler.
    
    Args:
        command: Main command to execute
        args: Additional arguments for the command
        json_output: Whether to format output as JSON
        
    Returns:
        Command result (dict for JSON, string for human-readable)
        
    Raises:
        ValueError: If command is unknown or invalid
    """
    if command not in COMMAND_HANDLERS:
        raise ValueError(f"Unknown command: {command}. Available commands: {', '.join(COMMAND_HANDLERS.keys())}")
    
    handler = COMMAND_HANDLERS[command]
    return handler(args, json_output=json_output)

#-#
