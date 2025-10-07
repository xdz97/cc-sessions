#!/usr/bin/env node

// ===== IMPORTS ===== //

/// ===== STDLIB ===== ///
const fs = require('fs');
const path = require('path');
const https = require('https');
///-///

/// ===== 3RD-PARTY ===== ///
///-///

/// ===== LOCAL ===== ///
const { editState, PROJECT_ROOT, loadConfig, SessionsProtocol, getTaskFilePath, isDirectoryTask } = require('./shared_state.js');
///-///

//-//

// ===== GLOBALS ===== //
const sessionsDir = path.join(PROJECT_ROOT, 'sessions');
let STATE = null;
const CONFIG = loadConfig();
const developerName = CONFIG.environment?.developer_name || 'developer';

// Initialize context
let context = `You are beginning a new context window with the developer, ${developerName}.\n\n`;

// Quick configuration checks
let needsSetup = false;
const quickChecks = [];
//-//

/*
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗██████╗██████╗██████╗██████╗ █████╗ ██╗  ██╗      ██████╗██████╗ █████╗ █████╗ ██████╗ ║
║ ██╔═══╝██╔═══╝██╔═══╝██╔═══╝╚═██╔═╝██╔══██╗███╗ ██║      ██╔═══╝╚═██╔═╝██╔══██╗██╔═██╗╚═██╔═╝ ║
║ ██████╗█████╗ ██████╗██████╗  ██║  ██║  ██║████╗██║      ██████╗  ██║  ███████║█████╔╝  ██║   ║
║ ╚═══██║██╔══╝ ╚═══██║╚═══██║  ██║  ██║  ██║██╔████║      ╚═══██║  ██║  ██╔══██║██╔═██╗  ██║   ║
║ ██████║██████╗██████║██████║██████╗╚█████╔╝██║╚███║      ██████║  ██║  ██║  ██║██║ ██║  ██║   ║
║ ╚═════╝╚═════╝╚═════╝╚═════╝╚═════╝ ╚════╝ ╚═╝ ╚══╝      ╚═════╝  ╚═╝  ╚═╝  ╚═╝╚═╝ ╚═╝  ╚═╝   ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
SessionStart Hook

Initializes session state and loads task context:
- Checks for required components (daic command, tiktoken)
- Clears session warning flags and stale state
- Loads current task or lists available tasks
- Updates task status from pending to in-progress
*/

// ===== FUNCTIONS ===== //

async function readStdin() {
    return new Promise((resolve) => {
        let data = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', chunk => data += chunk);
        process.stdin.on('end', () => {
            try {
                resolve(JSON.parse(data));
            } catch (e) {
                resolve({});
            }
        });
    });
}

function parseIndexFile(indexPath) {
    if (!fs.existsSync(indexPath)) {
        return null;
    }

    try {
        const content = fs.readFileSync(indexPath, 'utf8');
        const lines = content.split('\n');

        // Extract frontmatter using simple string parsing (like task files)
        const metadata = {};
        if (lines.length > 0 && lines[0] === '---') {
            for (let i = 1; i < lines.length; i++) {
                if (lines[i] === '---') {
                    break;
                }
                if (lines[i].includes(':')) {
                    const [key, ...valueParts] = lines[i].split(':');
                    metadata[key.trim()] = valueParts.join(':').trim();
                }
            }
        }

        // Extract task lines (those starting with - `)
        const taskLines = [];
        for (const line of lines) {
            if (line.trim().startsWith('- `')) {
                taskLines.push(line.trim());
            }
        }

        return [metadata, taskLines];
    } catch (error) {
        return null;
    }
}

function listOpenTasksGrouped() {
    const tasksDir = path.join(PROJECT_ROOT, 'sessions', 'tasks');
    const indexesDir = path.join(tasksDir, 'indexes');

    // Helper to get status from a task file
    function getTaskStatus(taskPath) {
        try {
            const content = fs.readFileSync(taskPath, 'utf8');
            const lines = content.split('\n').slice(0, 10);
            for (const line of lines) {
                if (line.startsWith('status:')) {
                    const status = line.split(':')[1].trim();
                    if (status !== 'complete') {
                        return status;
                    }
                }
            }
        } catch (error) {
            // Ignore read errors
        }
        return null;
    }

    // Step 1: Collect all .md files directly under tasks/ (exclude TEMPLATE.md)
    const fileTasksMap = {}; // name -> status
    if (fs.existsSync(tasksDir)) {
        const files = fs.readdirSync(tasksDir)
            .filter(f => f.endsWith('.md') && f !== 'TEMPLATE.md')
            .sort();

        for (const file of files) {
            const filePath = path.join(tasksDir, file);
            const status = getTaskStatus(filePath);
            if (status) {
                fileTasksMap[file] = status;
            }
        }
    }

    // Step 2: Collect all subdirectories (exclude indexes/ and done/)
    const dirTasksMap = {}; // dirname -> {status, subtasks: []}
    if (fs.existsSync(tasksDir)) {
        const dirs = fs.readdirSync(tasksDir)
            .filter(item => {
                const itemPath = path.join(tasksDir, item);
                return fs.statSync(itemPath).isDirectory() && !['done', 'indexes'].includes(item);
            })
            .sort();

        for (const dir of dirs) {
            const readmePath = path.join(tasksDir, dir, 'README.md');
            if (fs.existsSync(readmePath)) {
                const status = getTaskStatus(readmePath);
                if (status) {
                    dirTasksMap[dir] = { status, subtasks: [] };

                    // Collect subtasks
                    const subtaskFiles = fs.readdirSync(path.join(tasksDir, dir))
                        .filter(f => f.endsWith('.md') && !['TEMPLATE.md', 'README.md'].includes(f))
                        .sort();

                    for (const subtask of subtaskFiles) {
                        const subtaskPath = path.join(tasksDir, dir, subtask);
                        const subtaskStatus = getTaskStatus(subtaskPath);
                        if (subtaskStatus) {
                            dirTasksMap[dir].subtasks.push({
                                name: `${dir}/${subtask}`,
                                status: subtaskStatus
                            });
                        }
                    }
                }
            }
        }
    }

    // Step 3: Parse index files
    const indexInfo = {};
    if (fs.existsSync(indexesDir)) {
        const indexFiles = fs.readdirSync(indexesDir)
            .filter(f => f.endsWith('.md'))
            .sort();

        for (const indexFile of indexFiles) {
            const result = parseIndexFile(path.join(indexesDir, indexFile));
            if (result) {
                const [metadata, taskLines] = result;
                if (metadata && metadata.index) {
                    const indexId = metadata.index;
                    indexInfo[indexId] = {
                        name: metadata.name || indexId,
                        description: metadata.description || '',
                        tasks: []
                    };

                    // Extract task names from the lines
                    for (const line of taskLines) {
                        if (line.includes('`')) {
                            try {
                                const start = line.indexOf('`') + 1;
                                const end = line.indexOf('`', start);
                                let task = line.substring(start, end);
                                indexInfo[indexId].tasks.push(task);
                            } catch (error) {
                                continue;
                            }
                        }
                    }
                }
            }
        }
    }

    // Step 4: For each index, match against file tasks
    for (const indexId in indexInfo) {
        const validTasks = [];
        for (const task of indexInfo[indexId].tasks) {
            if (task in fileTasksMap) {
                validTasks.push({ name: task, status: fileTasksMap[task] });
                delete fileTasksMap[task]; // Remove from unindexed
            }
        }
        indexInfo[indexId].tasks = validTasks;
    }

    // Step 5: For each index, match against directory tasks and expand
    for (const indexId in indexInfo) {
        const expandedTasks = [];
        for (const task of indexInfo[indexId].tasks) {
            expandedTasks.push(task); // Keep existing file tasks
        }

        // Check the original task list again for directories
        const originalTasks = [];
        if (fs.existsSync(indexesDir)) {
            for (const indexFile of fs.readdirSync(indexesDir).filter(f => f.endsWith('.md'))) {
                const result = parseIndexFile(path.join(indexesDir, indexFile));
                if (result) {
                    const [metadata, taskLines] = result;
                    if (metadata && metadata.index === indexId) {
                        for (const line of taskLines) {
                            if (line.includes('`')) {
                                const start = line.indexOf('`') + 1;
                                const end = line.indexOf('`', start);
                                originalTasks.push(line.substring(start, end));
                            }
                        }
                    }
                }
            }
        }

        for (const task of originalTasks) {
            // Check if it's a directory reference (with or without trailing /)
            const dirName = task.endsWith('/') ? task.slice(0, -1) : task;
            if (dirName in dirTasksMap) {
                // Add the directory itself with / suffix
                expandedTasks.push({ name: `${dirName}/`, status: dirTasksMap[dirName].status });
                // Add all subtasks
                for (const subtask of dirTasksMap[dirName].subtasks) {
                    expandedTasks.push(subtask);
                }
                delete dirTasksMap[dirName]; // Remove from unindexed
            }
        }

        indexInfo[indexId].tasks = expandedTasks;
    }

    // Step 6: Build output
    let output = "No active task set. Available tasks:\n\n";

    // Display indexed tasks
    const sortedIndexes = Object.entries(indexInfo).sort((a, b) => a[0].localeCompare(b[0]));
    for (const [indexId, info] of sortedIndexes) {
        if (info.tasks.length > 0) {
            output += `## ${info.name}\n`;
            if (info.description) {
                output += `${info.description}\n`;
            }
            for (const task of info.tasks) {
                output += `  • ${task.name} (${task.status})\n`;
            }
            output += "\n";
        }
    }

    // Display unindexed tasks (remaining in fileTasksMap and dirTasksMap)
    const unindexedTasks = [];
    for (const [name, status] of Object.entries(fileTasksMap)) {
        unindexedTasks.push({ name, status });
    }
    for (const [name, data] of Object.entries(dirTasksMap)) {
        unindexedTasks.push({ name: `${name}/`, status: data.status });
        for (const subtask of data.subtasks) {
            unindexedTasks.push(subtask);
        }
    }

    if (unindexedTasks.length > 0) {
        output += "## Uncategorized\n";
        unindexedTasks.sort((a, b) => a.name.localeCompare(b.name));
        for (const task of unindexedTasks) {
            output += `  • ${task.name} (${task.status})\n`;
        }
        output += "\n";
    }

    // Add startup instructions
    output += `To select a task:
- Type in one of your startup commands: ${JSON.stringify(CONFIG.trigger_phrases.task_startup)}
- Include the task file you would like to start using \`@\`
- Hit Enter to activate task startup
`;

    return output;
}

//-//

// ===== EXECUTION ===== //

async function main() {
    // Read stdin for hook input
    const hookInput = await readStdin();

    //!> 1. Clear flags and todos for new session
    await editState((s) => {
        s.flags.clearFlags();
        s.todos.clearActive();
        const restored = s.todos.restoreStashed();
        STATE = s;

        context += "Cleared session flags and active todos for new session.\n\n";

        if (restored > 0) {
            context += `Restored ${restored} stashed todos from previous session:\n\n${JSON.stringify(s.todos.active)}\n\nTo clear, use \`cd .claude/hooks && node -e "const {editState} = require('./shared_state.js'); editState(s => s.todos.clearStashed()).then(()=>process.exit(0))"\`\n\n`;
        }
    });
    //!<

    //!> 2. Nuke transcripts dir
    const transcriptsDir = path.join(sessionsDir, 'transcripts');
    if (fs.existsSync(transcriptsDir)) {
        try {
            fs.rmSync(transcriptsDir, { recursive: true, force: true });
        } catch (error) {
            // Ignore errors
        }
    }
    //!<

    //!> 3. Load current task or list available tasks
    // Check for active task
    const taskFile = STATE.current_task?.filePath;
    if (taskFile && fs.existsSync(taskFile)) {
        // Check if task status is pending and update to in-progress
        let taskContent = fs.readFileSync(taskFile, 'utf8');
        let taskUpdated = false;

        // Parse task frontmatter to check status
        if (taskContent.startsWith('---')) {
            const lines = taskContent.split('\n');
            for (let i = 1; i < lines.length; i++) {
                if (lines[i] === '---') {
                    break;
                }
                if (lines[i].startsWith('status: pending')) {
                    lines[i] = 'status: in-progress';
                    taskUpdated = true;
                    // Write back the updated content
                    fs.writeFileSync(taskFile, lines.join('\n'), 'utf-8');
                    taskContent = lines.join('\n');
                    break;
                }
            }

            // Output the full task state
            context += `Current task state:
\`\`\`json
${JSON.stringify(STATE.current_task.task_state, null, 2)}
\`\`\`

Loading task file: ${STATE.current_task.file}
${"=".repeat(60)}
${taskContent}
${"=".repeat(60)}

`;
        }

        context += `Since you are resuming an in-progress task, follow these instructions:

    1. Analyze the task requirements and work completed thoroughly
    2. Analyze any next steps itemized in the task file and, if necessary, ask any questions from the user for clarification.
    3. Propose implementation plan with structured format:

\`\`\`markdown
[PLAN: Implementation Approach]
Based on the task requirements, I propose the following implementation:

□ [Specific action 1]
  → [Expanded explanation of what this involves]

□ [Specific action 2]
  → [Expanded explanation of what this involves]

□ [Specific action 3]
  → [Expanded explanation of what this involves]

To approve these todos, you may use any of your implementation mode trigger phrases:
${JSON.stringify(CONFIG.trigger_phrases.implementation_mode)}
\`\`\`

3. Iterate based on user feedback until approved
4. Upon approval, convert proposed todos to TodoWrite exactly as written

**IMPORTANT**: Until your todos are approved, you are seeking the user's approval of an explicitly proposed and properly explained list of execution todos. Besides answering user questions during discussion, your messages should end with an expanded explanation of each todo, the clean list of todos, and **no further messages**.

**For the duration of the task**:
- Discuss before implementing
- Constantly seek user input and approval

Once approved, remember:
- *Immediately* load your proposed todo items *exactly* as you proposed them using ToDoWrite
- Work logs are maintained by the logging agent (not manually)

After completion of the last task in any todo list:
- *Do not* try to run any write-based tools (you will be automatically put into discussion mode)
- Repeat todo proposal and approval workflow for any additional write/edit-based work`;
    } else {
        context += listOpenTasksGrouped();
    }
    //!<

    //!> 4. Check cc-sessions version
    try {
        // Check local version from package.json
        let currentVersion = null;
        const pkgPath = path.join(__dirname, '..', '..', '..', 'package.json');
        if (fs.existsSync(pkgPath)) {
            const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
            currentVersion = pkg.version;
        }

        // Check npm registry for latest version
        await new Promise((resolve) => {
            https.get('https://registry.npmjs.org/cc-sessions/latest', {
                timeout: 2000
            }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        const latest = JSON.parse(data);
                        const latestVersion = latest.version;
                        if (currentVersion && currentVersion !== latestVersion) {
                            context += `Update available for cc-sessions: ${currentVersion} → ${latestVersion}. Run \`npm install -g cc-sessions\` to update.`;
                        }
                        resolve();
                    } catch (e) {
                        resolve();
                    }
                });
            }).on('error', () => resolve());

            // Timeout after 2 seconds
            setTimeout(resolve, 2000);
        });
    } catch (error) {
        // Ignore version check errors
    }
    //!<

    //-//

    // Output in JSON format as expected by Claude Code hooks
    const output = {
        hookSpecificOutput: {
            hookEventName: "SessionStart",
            additionalContext: context
        }
    };

    console.log(JSON.stringify(output));
    process.exit(0);
}

// Run main function
main().catch(error => {
    console.error(JSON.stringify({
        hookSpecificOutput: {
            hookEventName: "SessionStart",
            additionalContext: `Error in session start hook: ${error.message}`
        }
    }));
    process.exit(1);
});
