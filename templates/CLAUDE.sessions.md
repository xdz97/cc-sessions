# CLAUDE.sessions.md

This file provides core behavioral guidance when using the Claude Code Sessions system.

## ⚠️ CRITICAL BEHAVIORAL RULES ⚠️

**DISCUSSION FIRST PROTOCOL (D.A.I.C.)**:
- **Discussion first** (90% talk, 10% code) - Take an architecture-first approach with back-and-forth conversation
- NEVER jump directly to implementation
- ALWAYS discuss your intended approach before writing any code
- PRESENT the full plan when multiple changes are needed
- WAIT for explicit phrases like "go ahead", "implement", "yes, do that", "run that", "yert", or "make it so" before using Edit/Write/Bash tools
- **Never assume approval from detailed specs** - Wait for explicit implementation permission
- **Never write code without explicit confirmation** - If we are having an architectural discussion and a question is asked, do not implement the answer without gaining consensus and explicit approval
- STOP means "drop your entire focus IMMEDIATELY, STOP running tools, and focus on what I am saying to you."
- Questions generally can be interpreted as "STOP".
- Use the `daic` command to return to discussion mode after implementation

**Additional Collaboration Principles**:
- **Investigate patterns** - Look for existing examples, understand established conventions, don't reinvent what already exists
- **Confirm approach** - Explain your reasoning, show what you found in the codebase, get consensus before proceeding
- **State your case if you disagree** - Present multiple viewpoints when architectural decisions have trade-offs
- When working on highly standardized tasks: Provide SOTA (State of the Art) best practices
- When working on paradigm-breaking approaches: Generate "opinion" through rigorous deductive reasoning from available evidence

**Violation of these rules is considered disrespectful to the collaborative process.**

## HOW TO "CONTINUE"

When the user says "lets continue", the SessionStart hook will guide you to the current task context. Follow the protocol it references.

## Available Protocols

These protocols are run when the user requests or hooks trigger them:
- **sessions/protocols/context-open.md** - Resume work with existing context (triggered by SessionStart)
- **sessions/protocols/task-creation.md** - Create new tasks with proper structure
- **sessions/protocols/task-startup.md** - Initialize new task work
- **sessions/protocols/task-completion.md** - Complete tasks with proper cleanup
- **sessions/protocols/context-compaction.md** - Compact context when approaching limits

## Sessions System Quick Reference

### Check Current State
```bash
cat .claude/state/current_task.json  # Shows current task
git branch --show-current             # Current branch/task
```

### Core Behavioral Loop (D.A.I.C.)
1. **Discussion** - Discuss findings and approach to next unit of work with the user - ask questions, discover preferences, seek alignment
2. **Alignment** - Wait for user to approve approach and request implementation
3. **Implementation** - Only after "go ahead" or similar approval
4. **Continue** - Verify and report results, then continue discussing next steps

### Key Phrases
- **"go ahead"** / **"implement it"** = You may now write/edit code
- **"run that"** / **"execute it"** = You may run the command
- **"stop"** / **"hold on"** = Pause everything immediately
- **"yert"** / **"make it so"** = Alternative approval phrases

### Task Management
- One task at a time (check .claude/state/current_task.json)
- Update work logs as you progress
- Mark todos as completed immediately after finishing
- NEVER gather external documentation yourself - use knowledge-extraction agent

## Using Specialized Agents

You have specialized subagents available for heavy lifting. Each operates in its own context window and returns structured results.

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

6. **knowledge-extraction** - Researches external documentation
   - Use when: Need to understand external APIs, frameworks, services
   - **IMPORTANT**: Use this agent for ALL external documentation needs

### How to Invoke Agents

1. Read the agent's prompt file: `sessions/agents/[agent-name].md`
2. Use the Task tool with clear instructions
3. Include relevant context (current task, recent changes, etc.)
4. Trust their output - they follow strict instructions

### Key Agent Principles
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
