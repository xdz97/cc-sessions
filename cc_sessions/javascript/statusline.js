#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { loadState, editState, Mode, Model, PROJECT_ROOT } = require('../hooks/shared_state.js');

// Colors/styles
const green = '\033[38;5;114m';
const orange = '\033[38;5;215m';
const red = '\033[38;5;203m';
const gray = '\033[38;5;242m';
const lGray = '\033[38;5;250m';
const cyan = '\033[38;5;111m';
const purple = '\033[38;5;183m';
const reset = '\033[0m';

function findGitRepo(startPath) {
    let current = startPath;
    while (current !== path.dirname(current)) {
        const gitPath = path.join(current, '.git');
        if (fs.existsSync(gitPath)) {
            return gitPath;
        }
        current = path.dirname(current);
    }
    return null;
}

function main() {
    // Read JSON input from stdin
    let inputData = '';
    try {
        inputData = fs.readFileSync(0, 'utf-8');
    } catch {
        // No stdin, use defaults
        inputData = '{}';
    }

    let data = {};
    try {
        data = JSON.parse(inputData);
    } catch {
        data = {};
    }

    const cwd = data.cwd || '.';
    const modelName = data.model?.display_name || 'unknown';
    const sessionId = data.session_id || 'unknown';
    const transcriptPath = data.transcript_path || null;

    const taskDir = path.join(PROJECT_ROOT, 'sessions', 'tasks');

    // Determine model and context limit
    let currModel = Model.UNKNOWN;
    let contextLimit = 160000;

    if (modelName.toLowerCase().includes('[1m]')) {
        contextLimit = 800000;
    }
    if (modelName.toLowerCase().includes('sonnet')) {
        currModel = Model.SONNET;
    } else if (modelName.toLowerCase().includes('opus')) {
        currModel = Model.OPUS;
    }

    // Update model in shared state
    const state = loadState();
    if (!state || state.model !== currModel) {
        editState(s => {
            s.model = currModel;
        });
    }

    // Pull context length from transcript
    let contextLength = null;

    if (transcriptPath && fs.existsSync(transcriptPath)) {
        try {
            const lines = fs.readFileSync(transcriptPath, 'utf-8').split('\n');
            let mostRecentUsage = null;
            let mostRecentTimestamp = null;

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const lineData = JSON.parse(line);
                    // Skip sidechain entries (subagent calls)
                    if (lineData.isSidechain) continue;

                    // Check for usage data in main-chain messages
                    if (lineData.message?.usage) {
                        const timestamp = lineData.timestamp;
                        if (timestamp && (!mostRecentTimestamp || timestamp > mostRecentTimestamp)) {
                            mostRecentTimestamp = timestamp;
                            mostRecentUsage = lineData.message.usage;
                        }
                    }
                } catch {
                    continue;
                }
            }

            // Calculate context length (input + cache tokens only, NOT output)
            if (mostRecentUsage) {
                contextLength = (mostRecentUsage.input_tokens || 0) +
                               (mostRecentUsage.cache_read_input_tokens || 0) +
                               (mostRecentUsage.cache_creation_input_tokens || 0);
            }
        } catch {
            // Ignore errors
        }
    }

    // Use context_length and context_limit to calculate context percentage
    if (contextLength && contextLength < 17000) {
        contextLength = 17000;
    }

    let progressPct = '0.0';
    let progressPctInt = 0;

    if (contextLength && contextLimit) {
        const pct = (contextLength * 100) / contextLimit;
        progressPct = pct.toFixed(1);
        progressPctInt = Math.floor(pct);
        if (progressPctInt > 100) {
            progressPct = '100.0';
            progressPctInt = 100;
        }
    }

    // Format token counts in 'k'
    const formattedTokens = contextLength ? `${Math.floor(contextLength / 1000)}k` : '17k';
    const formattedLimit = contextLimit ? `${Math.floor(contextLimit / 1000)}k` : '160k';

    // Progress bar blocks (0-10)
    const filledBlocks = Math.min(Math.floor(progressPctInt / 10), 10);
    const emptyBlocks = 10 - filledBlocks;

    // Choose color based on percentage
    let barColor = green;
    if (progressPctInt >= 80) {
        barColor = red;
    } else if (progressPctInt >= 50) {
        barColor = orange;
    }

    // Build progress bar string
    const progressBar =
        barColor + '█'.repeat(filledBlocks) +
        gray + '░'.repeat(emptyBlocks) +
        reset + ` ${lGray}${progressPct}% (${formattedTokens}/${formattedLimit})${reset}`;

    // Current task
    const currTask = state?.current_task?.name || null;

    // Current mode
    const currMode = state?.mode === Mode.GO ? 'Implementation' : 'Discussion';

    // Count edited & uncommitted files
    let totalEdited = 0;
    const gitPath = cwd === PROJECT_ROOT ? path.join(PROJECT_ROOT, '.git') : findGitRepo(path.resolve(cwd));

    if (gitPath && fs.existsSync(gitPath)) {
        try {
            // Count unstaged changes
            const unstaged = execSync(`git --git-dir "${gitPath}" --work-tree "${cwd}" diff --name-only`,
                                     { encoding: 'utf-8' }).trim();
            const unstagedCount = unstaged ? unstaged.split('\n').length : 0;

            // Count staged changes
            const staged = execSync(`git --git-dir "${gitPath}" --work-tree "${cwd}" diff --cached --name-only`,
                                   { encoding: 'utf-8' }).trim();
            const stagedCount = staged ? staged.split('\n').length : 0;

            totalEdited = unstagedCount + stagedCount;
        } catch {
            totalEdited = 0;
        }
    }

    // Count open tasks
    let openTaskCount = 0;
    let openTaskDirCount = 0;

    if (fs.existsSync(taskDir) && fs.statSync(taskDir).isDirectory()) {
        const items = fs.readdirSync(taskDir);
        for (const item of items) {
            const itemPath = path.join(taskDir, item);
            const stat = fs.statSync(itemPath);
            if (stat.isFile() && item !== 'TEMPLATE.md' && item.endsWith('.md')) {
                openTaskCount++;
            }
            if (stat.isDirectory() && item !== 'done') {
                openTaskDirCount++;
            }
        }
    }

    // Final output
    // Line 1
    const contextPart = progressBar || `${gray}No context usage data${reset}`;
    const taskPart = currTask ?
        `${cyan}Task: ${currTask}${reset}` :
        `${cyan}Task: ${gray}None loaded${reset}`;
    console.log(contextPart + ' | ' + taskPart);

    // Line 2
    console.log(
        `${purple}Mode: ${currMode}${reset}` + ' | ' +
        `${orange}✎ ${totalEdited} files to commit${reset}` + ' | ' +
        `${cyan}Open Tasks: ${openTaskCount + openTaskDirCount}${reset}`
    );
}

if (require.main === module) {
    main();
}