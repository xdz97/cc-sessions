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
const CONFIG = loadConfig();
const STATE = loadState();

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

function handleKickstartCommand(args, jsonOutput = false, fromSlash = false) {
    /**
     * Handle kickstart-specific commands for onboarding flow.
     *
     * Usage:
     *     kickstart next      - Load next module chunk
     *     kickstart complete  - Exit kickstart mode
     */
    if (!args || args.length === 0) {
        return formatKickstartHelp(jsonOutput);
    }

    const command = args[0].toLowerCase();
    const commandArgs = args.slice(1);

    if (command === 'next') {
        return loadNextModule(jsonOutput);
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
        'complete': 'Exit kickstart mode and clean up files'
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
    const kickstartMeta = STATE.metadata?.kickstart;

    if (!kickstartMeta) {
        const errorMsg = 'Error: No kickstart metadata found. This is a bug.';
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    const sequence = kickstartMeta.sequence;
    const currentIndex = kickstartMeta.current_index;
    const completed = kickstartMeta.completed || [];

    if (!sequence) {
        const errorMsg = 'Error: No kickstart sequence found. This is a bug.';
        if (jsonOutput) {
            return { error: errorMsg };
        }
        return errorMsg;
    }

    // Mark current as completed
    const currentFile = sequence[currentIndex];

    // Move to next
    const nextIndex = currentIndex + 1;

    // Check if we've reached the end
    if (nextIndex >= sequence.length) {
        return completeKickstart(jsonOutput);
    }

    const nextFile = sequence[nextIndex];

    // Update state
    editState(s => {
        s.metadata.kickstart.current_index = nextIndex;
        s.metadata.kickstart.completed.push(currentFile);
        s.metadata.kickstart.last_active = new Date().toISOString();
        return s;
    });

    // Load next protocol
    const protocolContent = loadProtocolFile(`kickstart/${nextFile}`);

    if (jsonOutput) {
        return {
            success: true,
            next_file: nextFile,
            protocol: protocolContent
        };
    }

    return protocolContent;
}

function completeKickstart(jsonOutput = false) {
    /**Exit kickstart mode, clean up files, and return cleanup instructions.*/
    // Switch to implementation mode if in discussion mode
    if (STATE.mode === Mode.NO) {
        editState(s => {
            s.mode = Mode.GO;
        });
    }

    // Delete kickstart files immediately
    const sessionsDir = path.join(PROJECT_ROOT, 'sessions');

    // 1. Delete kickstart hook (check both language variants)
    const pyHook = path.join(sessionsDir, 'hooks', 'kickstart_session_start.py');
    const jsHook = path.join(sessionsDir, 'hooks', 'kickstart_session_start.js');

    let isPython = true;
    if (fs.existsSync(pyHook)) {
        fs.unlinkSync(pyHook);
        isPython = true;
    } else if (fs.existsSync(jsHook)) {
        fs.unlinkSync(jsHook);
        isPython = false;
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

    // 4. Clear kickstart metadata
    editState(s => {
        delete s.metadata.kickstart;
        return s;
    });

    // Generate language-specific cleanup instructions based on which hook was found
    let instructions;
    if (isPython) {
        instructions = `Kickstart complete!

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/api/router.py
□ Remove 'kickstart': handle_kickstart_command from COMMAND_HANDLERS in router.py
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/api/kickstart_commands.py

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install.`;
    } else { // JavaScript
        instructions = `Kickstart complete!

I've deleted the kickstart protocols, hook, and setup task. Now you need to complete the cleanup by using TodoWrite to add these todos immediately, then executing them:

□ Remove kickstart import from sessions/api/router.js
□ Remove 'kickstart': handleKickstartCommand from COMMAND_HANDLERS in router.js
□ Remove kickstart SessionStart hook entry from .claude/settings.json
□ Delete sessions/api/kickstart_commands.js

After completing these todos, kickstart will be fully removed. These files won't exist in future package installations since users get fresh copies during install.`;
    }

    if (jsonOutput) {
        return {
            success: true,
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
