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

/// ===== CI DETECTION ===== ///
function isCIEnvironment() {
    // Check if running in a CI environment (GitHub Actions)
    const ciIndicators = [
        'GITHUB_ACTIONS',         // GitHub Actions
        'GITHUB_WORKFLOW',        // GitHub Actions workflow
        'CI',                     // Generic CI indicator (set by GitHub Actions)
        'CONTINUOUS_INTEGRATION', // Generic CI (alternative)
    ];
    return ciIndicators.some(indicator => process.env[indicator]);
}

// Skip kickstart session start hook in CI environments
if (isCIEnvironment()) {
    process.exit(0);
}
///-///

/// ===== MODULE SEQUENCES ===== ///
const FULL_MODE_SEQUENCE = [
    '01-discussion.md',
    '02-implementation.md',
    '03-tasks-overview.md',
    '04-task-creation.md',
    '05-task-startup.md',
    '06-task-completion.md',
    '07-compaction.md',
    '08-agents.md',
    '09-api.md',
    '10-advanced.md',
    '11-graduation.md'
];

const SUBAGENTS_MODE_SEQUENCE = [
    '01-agents-only.md'
];
///-///

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

Handles onboarding flow for users who chose kickstart in installer:
- Checks for kickstart metadata (should ALWAYS exist if this hook is running)
- Loads first module on first run, resumes from current_index on subsequent runs
- Sequences determined by mode (full or subagents)
*/

// ===== EXECUTION ===== //

//!> 1. Load state and check kickstart metadata
const STATE = loadState();

// Get kickstart metadata (should ALWAYS exist if this hook is running)
const kickstartMeta = STATE.metadata?.kickstart;
if (!kickstartMeta) {
    // This is a BUG - fail loudly
    console.log(JSON.stringify({
        hookSpecificOutput: {
            hookEventName: 'SessionStart',
            additionalContext: 'ERROR: kickstart_session_start hook fired but no kickstart metadata found. This is an installer bug.'
        }
    }));
    process.exit(1);
}

const mode = kickstartMeta.mode;  // 'full' or 'subagents'
if (!mode) {
    console.log(JSON.stringify({
        hookSpecificOutput: {
            hookEventName: 'SessionStart',
            additionalContext: 'ERROR: kickstart metadata exists but no mode specified. This is an installer bug.'
        }
    }));
    process.exit(1);
}
//!<

//!> 2. Initialize or load sequence
// Determine sequence based on mode
let sequence;
if (mode === 'full') {
    sequence = FULL_MODE_SEQUENCE;
} else if (mode === 'subagents') {
    sequence = SUBAGENTS_MODE_SEQUENCE;
} else {
    console.log(JSON.stringify({
        hookSpecificOutput: {
            hookEventName: 'SessionStart',
            additionalContext: `ERROR: Invalid kickstart mode '${mode}'. Expected 'full' or 'subagents'.`
        }
    }));
    process.exit(1);
}

// Initialize sequence on first run
let protocolContent;
if (!('sequence' in kickstartMeta)) {
    const { editState } = require(sharedStatePath);
    editState((s) => {
        s.metadata.kickstart.sequence = sequence;
        s.metadata.kickstart.current_index = 0;
        s.metadata.kickstart.completed = [];
        return s;
    });

    protocolContent = loadProtocolFile(`kickstart/${sequence[0]}`);
} else {
    // Load current protocol from sequence
    const currentIndex = kickstartMeta.current_index ?? 0;
    protocolContent = loadProtocolFile(`kickstart/${sequence[currentIndex]}`);
}
//!<

//!> 3. Append user instructions and output
protocolContent += `

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INSTRUCTIONS:
Just say 'kickstart' and press enter to begin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;

console.log(JSON.stringify({
    hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: protocolContent
    }
}));
process.exit(0);
//!<
