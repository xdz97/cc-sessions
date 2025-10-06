#!/usr/bin/env node

// ===== IMPORTS ===== #

// ===== STDLIB ===== //
//--//

// ===== LOCAL ===== //
const {
    handleStateCommand,
    handleModeCommand,
    handleFlagsCommand,
    handleStatusCommand,
    handleVersionCommand,
    handleTodosCommand
} = require('./state_commands.js');
const { handleConfigCommand } = require('./config_commands.js');
const { handleProtocolCommand } = require('./protocol_commands.js');
const { handleTaskCommand } = require('./task_commands.js');
const { handleKickstartCommand } = require('./kickstart_commands.js');
//--//

//-#

// ===== GLOBALS ===== #

const COMMAND_HANDLERS = {
    'protocol': handleProtocolCommand,
    'state': handleStateCommand,
    'mode': handleModeCommand,
    'flags': handleFlagsCommand,
    'status': handleStatusCommand,
    'version': handleVersionCommand,
    'config': handleConfigCommand,
    'todos': handleTodosCommand,
    'tasks': handleTaskCommand,
    'kickstart': handleKickstartCommand,
};

//-#

// ===== DECLARATIONS ===== #
//-#

// ===== CLASSES ===== #
//-#

// ===== FUNCTIONS ===== #

function routeCommand(command, args, jsonOutput = false, fromSlash = false) {
    /**
     * Route a command to the appropriate handler.
     *
     * Args:
     *     command: Main command to execute
     *     args: Additional arguments for the command
     *     jsonOutput: Whether to format output as JSON
     *     fromSlash: Whether the command came from a slash command
     *
     * Returns:
     *     Command result (dict for JSON, string for human-readable)
     *
     * Throws:
     *     Error: If command is unknown or invalid
     */

    // Special handling for slash command router
    if (command === 'slash') {
        if (!args || args.length === 0) {
            return formatSlashHelp();
        }

        const subsystem = args[0].toLowerCase();
        const subsystemArgs = args.length > 1 ? args.slice(1) : [];

        // Route to appropriate subsystem
        if (['tasks', 'state', 'config'].includes(subsystem)) {
            return routeCommand(subsystem, subsystemArgs, jsonOutput, true);
        } else if (subsystem === 'help') {
            return formatSlashHelp();
        } else {
            return `Unknown subsystem: ${subsystem}\n\nValid subsystems: tasks, state, config\n\nUse '/sessions help' for full usage information.`;
        }
    }

    if (!(command in COMMAND_HANDLERS)) {
        throw new Error(`Unknown command: ${command}. Available commands: ${Object.keys(COMMAND_HANDLERS).join(', ')}`);
    }

    const handler = COMMAND_HANDLERS[command];

    // Pass fromSlash to commands that support it
    if (['config', 'state', 'tasks'].includes(command)) {
        return handler(args, jsonOutput, fromSlash);
    } else {
        // For commands that don't support fromSlash, add it to args for backward compatibility
        if (fromSlash && !args.includes('--from-slash')) {
            args = [...args, '--from-slash'];
        }
        return handler(args, jsonOutput);
    }
}

function formatSlashHelp() {
    /**Format help output for unified /sessions slash command.*/
    const lines = [
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
    ];
    return lines.join('\n');
}

//-#

// ===== EXPORTS ===== #
module.exports = {
    routeCommand,
    formatSlashHelp
};
//-#