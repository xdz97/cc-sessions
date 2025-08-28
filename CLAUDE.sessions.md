# CLAUDE.sessions.md

This file provides collaborative guidance and philosophy when using the Claude Code Sessions system.

## Collaboration Philosophy

**Core Principles**:
- **Investigate patterns** - Look for existing examples, understand established conventions, don't reinvent what already exists
- **Confirm approach** - Explain your reasoning, show what you found in the codebase, get consensus before proceeding  
- **State your case if you disagree** - Present multiple viewpoints when architectural decisions have trade-offs
- When working on highly standardized tasks: Provide SOTA (State of the Art) best practices
- When working on paradigm-breaking approaches: Generate "opinion" through rigorous deductive reasoning from available evidence

## Task Management

### Best Practices
- One task at a time (check .claude/state/current_task.json)
- Update work logs as you progress  
- Mark todos as completed immediately after finishing

### Quick State Checks
```bash
cat .claude/state/current_task.json  # Shows current task
git branch --show-current             # Current branch/task
```

### current_task.json Format

**ALWAYS use this exact format for .claude/state/current_task.json:**
```json
{
  "task": "task-name",        // Just the task name, NO path, NO .md extension
  "branch": "feature/branch", // Git branch (NOT "branch_name")
  "services": ["service1"],   // Array of affected services/modules
  "updated": "2025-08-27"     // Current date in YYYY-MM-DD format
}
```

**Common mistakes to avoid:**
- ❌ Using `"task_file"` instead of `"task"`
- ❌ Using `"branch_name"` instead of `"branch"`  
- ❌ Including path like `"tasks/m-task.md"`
- ❌ Including `.md` file extension

## Using Specialized Agents

You have specialized subagents for heavy lifting. Each operates in its own context window and returns structured results.

### Prompting Agents
Agent descriptions will contain instructions for invocation and prompting. In general, it is safer to issue lightweight prompts. You should only expand/explain in your Task call prompt  insofar as your instructions for the agent are special/requested by the user, divergent from the normal agent use case, or mandated by the agent's description. Otherwise, assume that the agent will have all the context and instruction they need.

Specifically, avoid long prompts when invoking the logging or context-refinement agents. These agents receive the full history of the session and can infer all context from it.

### Available Agents

1. **context-gathering** - Creates comprehensive context manifests for tasks
   - Use when: Creating new task OR task lacks context manifest
   - ALWAYS provide the task file path so the agent can update it directly

2. **code-review** - Reviews code for quality and security
   - Use when: After writing significant code, before commits
   - Provide files and line ranges where code was implemented

3. **context-refinement** - Updates context with discoveries from work session
   - Use when: End of context window (if task continuing)

4. **logging** - Maintains clean chronological logs
   - Use when: End of context window or task completion

5. **service-documentation** - Updates service CLAUDE.md files
   - Use when: After service changes

### Agent Principles
- **Delegate heavy work** - Let agents handle file-heavy operations
- **Be specific** - Give agents clear context and goals
- **One agent, one job** - Don't combine responsibilities

## Code Philosophy

### Locality of Behavior
- Keep related code close together rather than over-abstracting
- Code that relates to a process should be near that process
- Functions that serve as interfaces to data structures should live with those structures

### Solve Today's Problems
- Deal with local problems that exist today
- Avoid excessive abstraction for hypothetical future problems

### Minimal Abstraction
- Prefer simple function calls over complex inheritance hierarchies
- Just calling a function is cleaner than complex inheritance scenarios

### Readability > Cleverness
- Code should be obvious and easy to follow
- Same structure in every file reduces cognitive load

## Available Protocols

When needed, these protocols guide specific workflows:
- **sessions/protocols/task-creation.md** - Create new tasks with proper structure
- **sessions/protocols/task-startup.md** - Initialize new task work
- **sessions/protocols/task-completion.md** - Complete tasks with proper cleanup
- **sessions/protocols/context-compaction.md** - Compact context when approaching limits
