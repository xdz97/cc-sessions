#!/usr/bin/env node
/**
 * Parallel Agent Orchestrator
 *
 * Manages execution of multiple Task agents simultaneously to parallelize work.
 */

const { spawn } = require('child_process');
const path = require('path');

// Import from hooks
const { PROJECT_ROOT } = require('./hooks/shared_state.js');

/**
 * Status of a parallel agent task
 */
class AgentStatus {
    static PENDING = 'pending';
    static RUNNING = 'running';
    static COMPLETED = 'completed';
    static FAILED = 'failed';
}

/**
 * Represents a single agent task in parallel execution
 */
class AgentTask {
    /**
     * @param {Object} params
     * @param {string} params.id - Task identifier
     * @param {string} params.agentName - Name of the agent
     * @param {string} params.prompt - Prompt to send to the agent
     * @param {string} [params.status] - Current status
     * @param {number} [params.processId] - Process ID
     * @param {string} [params.output] - Output from the task
     * @param {string} [params.error] - Error from the task
     * @param {number} [params.exitCode] - Exit code
     * @param {number} [params.startTime] - Start timestamp
     * @param {number} [params.endTime] - End timestamp
     */
    constructor({
        id,
        agentName,
        prompt,
        status = AgentStatus.PENDING,
        processId = null,
        output = '',
        error = '',
        exitCode = null,
        startTime = null,
        endTime = null
    }) {
        this.id = id;
        this.agentName = agentName;
        this.prompt = prompt;
        this.status = status;
        this.processId = processId;
        this.output = output;
        this.error = error;
        this.exitCode = exitCode;
        this.startTime = startTime;
        this.endTime = endTime;
    }

    /**
     * Calculate task duration in seconds
     * @returns {number|null}
     */
    get duration() {
        if (this.startTime !== null && this.endTime !== null) {
            return this.endTime - this.startTime;
        }
        return null;
    }

    /**
     * Convert to dictionary for serialization
     * @returns {Object}
     */
    toDict() {
        return {
            id: this.id,
            agentName: this.agentName,
            prompt: this.prompt,
            status: this.status,
            processId: this.processId,
            output: this.output,
            error: this.error,
            exitCode: this.exitCode,
            startTime: this.startTime,
            endTime: this.endTime,
            duration: this.duration
        };
    }
}

/**
 * Result of parallel orchestration execution
 */
class OrchestrationResult {
    /**
     * @param {Object} params
     * @param {number} params.totalTasks - Total number of tasks
     * @param {number} params.completed - Number of completed tasks
     * @param {number} params.failed - Number of failed tasks
     * @param {number} params.totalDuration - Total execution time
     * @param {AgentTask[]} [params.tasks] - List of tasks
     */
    constructor({
        totalTasks,
        completed,
        failed,
        totalDuration,
        tasks = []
    }) {
        this.totalTasks = totalTasks;
        this.completed = completed;
        this.failed = failed;
        this.totalDuration = totalDuration;
        this.tasks = tasks;
    }

    /**
     * Convert to dictionary for serialization
     * @returns {Object}
     */
    toDict() {
        return {
            totalTasks: this.totalTasks,
            completed: this.completed,
            failed: this.failed,
            totalDuration: this.totalDuration,
            tasks: this.tasks.map(task => task.toDict())
        };
    }

    /**
     * Human-readable summary
     * @returns {string}
     */
    toString() {
        const lines = [
            '\n=== Parallel Orchestration Results ===',
            `Total Tasks: ${this.totalTasks}`,
            `Completed: ${this.completed}`,
            `Failed: ${this.failed}`,
            `Total Duration: ${this.totalDuration.toFixed(2)}s`,
            '\nIndividual Task Results:'
        ];

        for (const task of this.tasks) {
            const statusSymbol = task.status === AgentStatus.COMPLETED ? '✓' : '✗';
            const durationStr = task.duration !== null ? `${task.duration.toFixed(2)}s` : 'N/A';
            lines.push(`  ${statusSymbol} ${task.agentName} (${task.id}): ${task.status} - ${durationStr}`);
        }

        return lines.join('\n');
    }
}

/**
 * Orchestrates multiple Task agents to run in parallel.
 *
 * This allows complex operations like code review to be split across
 * multiple agents analyzing different files/modules simultaneously.
 */
class ParallelAgentOrchestrator {
    /**
     * Initialize the orchestrator.
     *
     * @param {number} [maxConcurrent=4] - Maximum number of agents to run simultaneously
     */
    constructor(maxConcurrent = 4) {
        this.maxConcurrent = maxConcurrent;
        this.tasks = [];
        this.runningTasks = [];
    }

    /**
     * Add a task to the orchestration queue.
     *
     * @param {string} agentName - Name of the agent to invoke (e.g., 'code-review', 'context-gathering')
     * @param {string} prompt - The prompt to send to the agent
     * @param {string} [taskId] - Optional custom ID for the task
     * @returns {AgentTask} The created AgentTask
     */
    addTask(agentName, prompt, taskId = null) {
        if (!taskId) {
            taskId = `${agentName}_${this.tasks.length + 1}`;
        }

        const task = new AgentTask({
            id: taskId,
            agentName,
            prompt
        });
        this.tasks.push(task);
        return task;
    }

    /**
     * Start a Task agent process for the given task.
     *
     * @param {AgentTask} task - The task to execute
     * @returns {Promise<void>}
     * @private
     */
    async _startAgentProcess(task) {
        // TODO: This needs to invoke the Claude Code Task tool
        // For now, this is a placeholder that would need integration with Claude Code's API
        // In practice, this would call out to Claude Code's agent execution system

        // Placeholder command - would actually invoke Task tool through Claude Code
        const process = spawn('echo', [
            `[PLACEHOLDER] Running agent ${task.agentName} with prompt: ${task.prompt.slice(0, 50)}...`
        ]);

        task.processId = process.pid;
        task.status = AgentStatus.RUNNING;
        task.startTime = Date.now() / 1000; // Convert to seconds

        // Collect output
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        // Store the process for later polling
        task._process = process;
        task._stdout = stdout;
        task._stderr = stderr;
    }

    /**
     * Check status of running tasks and move completed ones.
     * @private
     */
    _pollRunningTasks() {
        const completed = [];

        for (const task of this.runningTasks) {
            const process = task._process;

            // Check if process has exited
            if (process && process.exitCode !== null) {
                task.status = process.exitCode === 0 ? AgentStatus.COMPLETED : AgentStatus.FAILED;
                task.endTime = Date.now() / 1000;
                task.exitCode = process.exitCode;
                task.output = task._stdout || '';
                task.error = task._stderr || '';
                completed.push(task);

                // Clean up process references
                delete task._process;
                delete task._stdout;
                delete task._stderr;
            } else if (!process) {
                // Simulate completion for placeholder implementation
                task.status = AgentStatus.COMPLETED;
                task.endTime = Date.now() / 1000;
                task.exitCode = 0;
                completed.push(task);
            }
        }

        // Remove completed tasks from running list
        for (const task of completed) {
            const index = this.runningTasks.indexOf(task);
            if (index !== -1) {
                this.runningTasks.splice(index, 1);
            }
        }
    }

    /**
     * Execute all queued tasks in parallel.
     *
     * @param {number} [timeout] - Optional timeout in seconds for the entire orchestration
     * @returns {Promise<OrchestrationResult>} Execution summary
     */
    async executeAll(timeout = null) {
        const startTime = Date.now() / 1000;
        const pendingTasks = this.tasks.filter(t => t.status === AgentStatus.PENDING);

        while (pendingTasks.length > 0 || this.runningTasks.length > 0) {
            // Check for timeouts
            if (timeout && (Date.now() / 1000 - startTime) > timeout) {
                // Mark all pending/running tasks as failed
                for (const task of [...pendingTasks, ...this.runningTasks]) {
                    if (task.status === AgentStatus.PENDING || task.status === AgentStatus.RUNNING) {
                        task.status = AgentStatus.FAILED;
                        task.error = 'Timeout exceeded';
                        task.endTime = Date.now() / 1000;
                    }
                }
                break;
            }

            // Start new tasks up to max_concurrent limit
            while (this.runningTasks.length < this.maxConcurrent && pendingTasks.length > 0) {
                const task = pendingTasks.shift();
                try {
                    await this._startAgentProcess(task);
                    this.runningTasks.push(task);
                } catch (error) {
                    task.status = AgentStatus.FAILED;
                    task.error = error.message;
                    task.endTime = Date.now() / 1000;
                }
            }

            // Poll running tasks for completion
            this._pollRunningTasks();

            // Small sleep to avoid busy-waiting
            if (this.runningTasks.length > 0) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        // Calculate results
        const totalDuration = Date.now() / 1000 - startTime;
        const completed = this.tasks.filter(t => t.status === AgentStatus.COMPLETED).length;
        const failed = this.tasks.filter(t => t.status === AgentStatus.FAILED).length;

        return new OrchestrationResult({
            totalTasks: this.tasks.length,
            completed,
            failed,
            totalDuration,
            tasks: [...this.tasks]
        });
    }

    /**
     * Convenience method to add tasks and execute them immediately.
     *
     * @param {Array<[string, string]>} taskDefinitions - Array of [agentName, prompt] tuples
     * @returns {Promise<OrchestrationResult>} Execution summary
     *
     * @example
     * const orchestrator = new ParallelAgentOrchestrator(3);
     * const result = await orchestrator.executeAndWait([
     *     ['code-review', 'Review src/auth/'],
     *     ['code-review', 'Review src/api/'],
     *     ['code-review', 'Review src/database/']
     * ]);
     */
    async executeAndWait(taskDefinitions) {
        for (const [agentName, prompt] of taskDefinitions) {
            this.addTask(agentName, prompt);
        }

        return await this.executeAll();
    }
}

/**
 * Perform parallel code review across multiple files/directories.
 *
 * @param {string[]} filePaths - List of file or directory paths to review
 * @param {number} [maxConcurrent=3] - Maximum number of reviews to run in parallel
 * @returns {Promise<OrchestrationResult>} All review results
 *
 * @example
 * const result = await parallelCodeReview([
 *     'src/auth/',
 *     'src/api/',
 *     'src/database/'
 * ]);
 * console.log(result.toString());
 */
async function parallelCodeReview(filePaths, maxConcurrent = 3) {
    const orchestrator = new ParallelAgentOrchestrator(maxConcurrent);

    for (const filePath of filePaths) {
        const prompt = `Perform a thorough code review of ${filePath}. Focus on security, performance, and code quality.`;
        const fileName = path.basename(filePath);
        orchestrator.addTask('code-review', prompt, `review_${fileName}`);
    }

    return await orchestrator.executeAll();
}

/**
 * Gather context for multiple tasks in parallel.
 *
 * @param {string[]} taskFiles - List of task file paths
 * @param {number} [maxConcurrent=3] - Maximum number of context gatherings to run in parallel
 * @returns {Promise<OrchestrationResult>} All context gathering results
 *
 * @example
 * const result = await parallelContextGathering([
 *     'sessions/tasks/h-implement-auth.md',
 *     'sessions/tasks/m-add-logging.md'
 * ]);
 */
async function parallelContextGathering(taskFiles, maxConcurrent = 3) {
    const orchestrator = new ParallelAgentOrchestrator(maxConcurrent);

    for (const taskFile of taskFiles) {
        const taskPath = path.parse(taskFile);
        const prompt = `Create a comprehensive context manifest for the task in ${taskFile}`;
        orchestrator.addTask('context-gathering', prompt, `context_${taskPath.name}`);
    }

    return await orchestrator.executeAll();
}

// Example usage and testing
async function main() {
    // Example: Parallel code review
    console.log('=== Example: Parallel Code Review ===');
    const result1 = await parallelCodeReview([
        'cc_sessions/javascript/hooks/',
        'cc_sessions/javascript/api/',
        'cc_sessions/protocols/'
    ], 2);
    console.log(result1.toString());

    // Example: Custom orchestration
    console.log('\n=== Example: Custom Orchestration ===');
    const orchestrator = new ParallelAgentOrchestrator(3);
    orchestrator.addTask('code-review', 'Review authentication module');
    orchestrator.addTask('code-review', 'Review API endpoints');
    orchestrator.addTask('logging', 'Consolidate task logs');

    const result2 = await orchestrator.executeAll();
    console.log(result2.toString());
    console.log(`\nJSON output:\n${JSON.stringify(result2.toDict(), null, 2)}`);
}

// Run examples if this file is executed directly
if (require.main === module) {
    main().catch(console.error);
}

// Exports
module.exports = {
    AgentStatus,
    AgentTask,
    OrchestrationResult,
    ParallelAgentOrchestrator,
    parallelCodeReview,
    parallelContextGathering
};
