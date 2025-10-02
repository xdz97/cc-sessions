#!/usr/bin/env node

// ===== IMPORTS ===== //

/// ===== STDLIB ===== ///
const fs = require('fs');
const path = require('path');
///-///

/// ===== 3RD-PARTY ===== ///
///-///

/// ===== LOCAL ===== ///
// Import from shared_state (same pattern as normal hooks)
const PROJECT_ROOT = path.resolve(__dirname, '../../../../..');
const sharedStatePath = path.join(PROJECT_ROOT, 'sessions', 'hooks', 'shared_state.js');
const { loadState } = require(sharedStatePath);
///-///

//-//

// ===== GLOBALS ===== //
//-//

// ===== FUNCTIONS ===== //

function loadProtocolFile(relativePath) {
    /**
     * Load protocol markdown from protocols directory.
     */
    const protocolPath = path.join(PROJECT_ROOT, 'sessions', 'protocols', relativePath);
    if (!fs.existsSync(protocolPath)) {
        return `Error: Protocol file not found: ${relativePath}`;
    }
    return fs.readFileSync(protocolPath, 'utf8');
}

//-//

/*
Kickstart SessionStart Hook

Handles onboarding flow for new users (noob flag = true):
- Checks noob flag and exits immediately if false (lets normal hooks run)
- Respects reminder dates for "later" option
- Loads entry protocol on first run
- Resumes kickstart progress from where user left off
*/

// ===== EXECUTION ===== //

//!> 1. Load state and check noob flag
const STATE = loadState();

// Not a noob? Exit immediately and let normal hooks run
if (!STATE.flags.noob) {
    process.exit(0);
}
//!<

//!> 2. Check reminder date
const reminderDate = STATE.metadata?.kickstart_reminder_date;
if (reminderDate) {
    if (new Date().toISOString() < reminderDate) {
        // Still in reminder period, use normal flow
        process.exit(0);
    }
}
//!<

//!> 3. Build context based on kickstart progress
const kickstartProgress = STATE.metadata?.kickstart_progress;
let context;

if (!kickstartProgress) {
    // First run - load entry protocol
    context = loadProtocolFile('kickstart/01-entry.md');
} else {
    // Resume from where we left off
    const mode = kickstartProgress.mode || 'full';
    const currentModule = kickstartProgress.current_module;

    context = `[Resuming Kickstart: ${mode} mode]\n\n`;
    context += loadProtocolFile(`kickstart/${mode}/${currentModule}.md`);
}
//!<

//!> 4. Output context and exit
console.log(JSON.stringify({
    hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: context
    }
}));
process.exit(0);
//!<
