#!/usr/bin/env node

// ===== IMPORTS ===== #

// ===== STDLIB ===== //
const fs = require('fs');
const path = require('path');
//--//

// ===== LOCAL ===== //
const { loadState, editState, loadConfig, PROJECT_ROOT, Mode } = require('../../hooks/shared_state.js');
//--//

//-#

// ===== GLOBALS ===== #

const FULL_MODE_SEQUENCE = [
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
];

const API_MODE_SEQUENCE = [
    '03-core-workflow',
    '04-task-protocols',
    '05-context-management',
    '06-configuration',
    '07-agent-customization',
    '08-advanced-concepts',
    '09-create-first-task',
    '10-graduation'
];

const SESHXPERT_SEQUENCE = [
    '03-quick-setup',
    '05-graduation'
];

//-#

// ===== FUNCTIONS ===== #

function formatConfigForDisplay(config) {
    /**Format config as readable markdown for kickstart display.*/
    return `**Current Configuration:**

**Trigger Phrases:**
- Implementation mode: ${config.trigger_phrases.implementation_mode}
- Discussion mode: ${config.trigger_phrases.discussion_mode}
- Task creation: ${config.trigger_phrases.task_creation}
- Task startup: ${config.trigger_phrases.task_startup}
- Task completion: ${config.trigger_phrases.task_completion}
- Context compaction: ${config.trigger_phrases.context_compaction}

**Git Preferences:**
- Default branch: ${config.git_preferences.default_branch}
- Has submodules: ${config.git_preferences.has_submodules}
- Add pattern: ${config.git_preferences.add_pattern}

**Environment:**
- Developer name: ${config.environment.developer_name}
- Project root: ${config.environment.project_root}`;
}

function loadProtocolFile(relativePath) {
    /**Load protocol markdown from protocols directory.*/
    const protocolPath = path.join(PROJECT_ROOT, 'sessions', 'protocols', relativePath);
    if (!fs.existsSync(protocolPath)) {
        return `Error: Protocol file not found: ${relativePath}`;
    }
    return fs.readFileSync(protocolPath, 'utf8');
}

function getModeSequence(mode) {
    /**Get the module sequence for a given mode.*/
    if (mode === 'full') {
        return FULL_MODE_SEQUENCE;
    } else if (mode === 'api') {
        return API_MODE_SEQUENCE;
    } else if (mode === 'seshxpert') {
        return SESHXPERT_SEQUENCE;
    } else {
        return [];
    }
}

function handleKickstartCommand(args, jsonOutput = false, fromSlash = false) {
    /**
     * Handle kickstart-specific commands for onboarding flow.
     *
     * Usage:
     *     kickstart next                  - Load next module chunk
     *     kickstart mode <mode>           - Initialize kickstart with selected mode
     *     kickstart remind <dd:hh>        - Set reminder date for "later" option
     *     kickstart complete              - Exit kickstart mode
     */
    if (!args || args.length === 0) {
        return formatKickstartHelp(jsonOutput);
    }

    const command = args[0].toLowerCase();
    const commandArgs = args.slice(1);

    if (command === 'next') {
        return loadNextModule(jsonOutput);
    } else if (command === 'mode') {
        if (commandArgs.length === 0) {
            const errorMsg = 'Error: mode requires argument (full|api|seshxpert)';
            if (jsonOutput) {
                return { error: errorMsg };
            }
            return errorMsg;
        }
        return setKickstartMode(commandArgs[0], jsonOutput);
    } else if (command === 'remind') {
        if (commandArgs.length === 0) {
            const errorMsg = 'Error: remind requires dd:hh format (e.g., 1:00 for tomorrow)';
            if (jsonOutput) {
                return { error: errorMsg };
            }
            return errorMsg;
        }
        return setReminder(commandArgs[0], jsonOutput);
    } else if (command === 'complete') {
        return completeKickstart(jsonOutput);
    } else {
        const errorMsg = `Unknown kickstart command: ${command}`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }
}

function formatKickstartHelp(jsonOutput) {
    /**Format help for kickstart commands.*/
    const commands = {
        'next': 'Load next module chunk based on current progress',
        'mode <mode>': 'Initialize kickstart with selected mode (full|api|seshxpert)',
        'remind <dd:hh>': "Set reminder date for 'later' option (e.g., 1:00 for tomorrow)",
        'complete': 'Exit kickstart mode and clear noob flag'
    };

    if (jsonOutput) {
        return { available_commands: commands };
    }

    const lines = ['Kickstart Commands:'];
    for (const [cmd, desc] of Object.entries(commands)) {
        lines.push(`  ${cmd}: ${desc}`);
    }
    return lines.join('\n');
}

function loadNextModule(jsonOutput = false) {
    /**Load next module chunk based on current progress.*/
    const STATE = loadState();
    const progress = STATE.metadata?.kickstart_progress || {};

    if (!progress || Object.keys(progress).length === 0) {
        const errorMsg = "Error: No kickstart progress found. Start with 'mode' command first.";
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    const mode = progress.mode || 'full';
    const current = progress.current_module;

    // Get sequence for current mode
    const sequence = getModeSequence(mode);

    if (sequence.length === 0) {
        const errorMsg = `Error: Invalid mode '${mode}'`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    // Find next module
    const currentIdx = sequence.indexOf(current);

    if (currentIdx === -1) {
        const errorMsg = `Error: Current module '${current}' not found in sequence`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    if (currentIdx >= sequence.length - 1) {
        // Reached end of sequence
        return completeKickstart(jsonOutput);
    }

    const nextModule = sequence[currentIdx + 1];

    // Update progress
    editState(s => {
        s.metadata.kickstart_progress.current_module = nextModule;
        if (!s.metadata.kickstart_progress.completed_modules) {
            s.metadata.kickstart_progress.completed_modules = [];
        }
        s.metadata.kickstart_progress.completed_modules.push(current);
        s.metadata.kickstart_progress.last_active = new Date().toISOString();
    });

    // Load protocol content
    let protocolContent = loadProtocolFile(`kickstart/${mode}/${nextModule}.md`);

    // Format with config if needed
    if (protocolContent.includes('{config}')) {
        const config = loadConfig();
        const configDisplay = formatConfigForDisplay(config);
        protocolContent = protocolContent.replace('{config}', configDisplay);
    }

    if (jsonOutput) {
        return {
            success: true,
            mode: mode,
            next_module: nextModule,
            protocol: protocolContent
        };
    }

    return protocolContent;
}

function setKickstartMode(modeStr, jsonOutput = false) {
    /**Initialize kickstart with selected mode.*/
    modeStr = modeStr.toLowerCase();

    if (!['full', 'api', 'seshxpert'].includes(modeStr)) {
        const errorMsg = `Error: Invalid mode '${modeStr}'. Use: full, api, or seshxpert`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    const sequence = getModeSequence(modeStr);
    const firstModule = sequence[0];

    editState(s => {
        s.metadata.kickstart_progress = {
            mode: modeStr,
            started: new Date().toISOString(),
            last_active: new Date().toISOString(),
            current_module: firstModule,
            completed_modules: [],
            agent_progress: {}
        };
    });

    // Load first module for selected mode
    let protocolContent = loadProtocolFile(`kickstart/${modeStr}/${firstModule}.md`);

    // Format with config if needed
    if (protocolContent.includes('{config}')) {
        const config = loadConfig();
        const configDisplay = formatConfigForDisplay(config);
        protocolContent = protocolContent.replace('{config}', configDisplay);
    }

    if (jsonOutput) {
        return {
            success: true,
            mode: modeStr,
            first_module: firstModule,
            protocol: protocolContent
        };
    }

    return protocolContent;
}

function setReminder(dateStr, jsonOutput = false) {
    /**Set reminder date for 'later' option.*/
    // Parse dd:hh format
    const parts = dateStr.split(':');
    if (parts.length !== 2) {
        const errorMsg = `Error: Invalid format '${dateStr}'. Use dd:hh (e.g., 1:00 for tomorrow)`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    const days = parseInt(parts[0], 10);
    const hours = parseInt(parts[1], 10);

    if (isNaN(days) || isNaN(hours)) {
        const errorMsg = `Error: Invalid format '${dateStr}'. Use dd:hh (e.g., 1:00 for tomorrow)`;
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    const reminderTime = new Date();
    reminderTime.setDate(reminderTime.getDate() + days);
    reminderTime.setHours(reminderTime.getHours() + hours);

    editState(s => {
        s.metadata.kickstart_reminder_date = reminderTime.toISOString();
    });

    const formattedTime = reminderTime.toISOString().slice(0, 16).replace('T', ' ');

    if (jsonOutput) {
        return {
            success: true,
            reminder_date: reminderTime.toISOString(),
            formatted: formattedTime
        };
    }

    return `Reminder set for ${formattedTime}. I'll ask about kickstart again then.`;
}

function completeKickstart(jsonOutput = false) {
    /**Exit kickstart mode, clean up files, and return cleanup instructions.*/
    const STATE = loadState();

    // Get install language (default to 'py' if not set)
    const installLang = STATE.metadata?.install_lang || 'py';

    // Switch to implementation mode if in discussion mode
    if (STATE.mode === Mode.NO) {
        editState(s => {
            s.mode = Mode.GO;
        });
    }

    // Delete kickstart files immediately
    const sessionsDir = path.join(PROJECT_ROOT, 'sessions');

    // 1. Delete kickstart hook (language-specific)
    const hookFile = installLang === 'py'
        ? path.join(sessionsDir, 'hooks', 'kickstart_session_start.py')
        : path.join(sessionsDir, 'hooks', 'kickstart_session_start.js');

    if (fs.existsSync(hookFile)) {
        fs.unlinkSync(hookFile);
    }

    // 2. Delete kickstart protocols directory
    const protocolsDir = path.join(sessionsDir, 'protocols', 'kickstart');
    if (fs.existsSync(protocolsDir)) {
        fs.rmSync(protocolsDir, { recursive: true, force: true });
    }

    // 3. Delete kickstart setup task (check both locations)
    let taskFile = path.join(sessionsDir, 'tasks', 'h-kickstart-setup.md');
    if (!fs.existsSync(taskFile)) {
        taskFile = path.join(sessionsDir, 'tasks', 'done', 'h-kickstart-setup.md');
    }

    if (fs.existsSync(taskFile)) {
        fs.unlinkSync(taskFile);
    }

    // 4. Clear noob flag and kickstart metadata
    editState(s => {
        s.flags.noob = false;
        delete s.metadata.kickstart_progress;
        delete s.metadata.kickstart_reminder_date;
    });

    // Generate language-specific cleanup instructions
    let instructions;
    if (installLang === 'py') {
        instructions = `Kickstart complete! The noob flag has been cleared.

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/scripts/api/router.py
□ Remove 'kickstart': handle_kickstart_command from COMMAND_HANDLERS in router.py
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/scripts/api/kickstart_commands.py

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install.`;
    } else { // 'js'
        instructions = `Kickstart complete! The noob flag has been cleared.

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/scripts/api/router.js
□ Remove 'kickstart': handleKickstartCommand from COMMAND_HANDLERS in router.js
□ Remove kickstart SessionStart hook entry from .claude/settings.json.js
□ Delete sessions/scripts/api/kickstart_commands.js

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install.`;
    }

    if (jsonOutput) {
        return {
            success: true,
            install_lang: installLang,
            instructions: instructions
        };
    }

    return instructions;
}

//-#

// ===== EXPORTS ===== #
module.exports = {
    handleKickstartCommand
};
//-#
