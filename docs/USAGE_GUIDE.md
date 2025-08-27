# Claude Code Sessions - Usage Guide

A comprehensive guide to using the Sessions framework for daily development with Claude Code.

## Table of Contents

1. [Understanding the Workflow](#understanding-the-workflow)
2. [Your First Task](#your-first-task)
3. [Daily Development Flow](#daily-development-flow)
4. [Working with Agents](#working-with-agents)
5. [Context Management](#context-management)
6. [Advanced Patterns](#advanced-patterns)

## Understanding the Workflow

### The D.A.I.C. Cycle

The Sessions framework enforces a natural development rhythm:

```
Discussion (90%) → Alignment → Implementation (10%) → Check → Discussion
```

This isn't restriction - it's liberation. By discussing first, you:
- Avoid costly refactors
- Leverage Claude's architectural knowledge
- Build consensus before committing code
- Maintain clear communication

### Key Mental Model

Think of Claude as your pair programmer who:
- **Must** understand the plan before coding
- **Can** delegate complex analysis to specialized agents
- **Will** track progress and context automatically
- **Won't** make changes without explicit approval

## Your First Task

### Step 1: Create the Task File

```bash
# Copy the template
cp sessions/tasks/TEMPLATE.md sessions/tasks/m-add-user-auth.md

# Edit with your requirements
vim sessions/tasks/m-add-user-auth.md
```

### Step 2: Fill Out Task Structure

```markdown
---
task: m-add-user-auth
branch: feature/user-auth
status: pending
started: 2025-01-20
modules: [auth, database, api]
---

# Add User Authentication

## Problem/Goal
Implement JWT-based authentication with refresh tokens

## Success Criteria
- [ ] User registration endpoint
- [ ] Login with JWT generation
- [ ] Refresh token mechanism
- [ ] Protected route middleware
- [ ] Tests with 80% coverage

## Context Manifest
[Will be created by context-gathering agent]

## Work Log
[Automatically maintained during work]
```

### Step 3: Start Working with Claude

```
You: Let's work on the user authentication task

Claude: I'll help with the user authentication task. Let me first gather context
        about your existing codebase to understand how to integrate this feature.
        
        [Uses context-gathering agent]
        [Loads task file and context manifest]
        
        Based on the context, I can see you have an Express API. Here's how
        I would approach adding JWT authentication:
        
        1. Install required packages (jsonwebtoken, bcrypt)
        2. Create auth middleware
        3. Add user model with password hashing
        4. Implement registration and login endpoints
        5. Add refresh token mechanism
        
        Should we start with the user model and database schema?

You: Yes, let's start there. Focus on PostgreSQL with Prisma.

Claude: [Discusses Prisma schema design, password hashing strategy]

You: go ahead

Claude: [Now switches to implementation mode and creates the code]
```

## Daily Development Flow

### Starting Your Day

1. **Check Current State**
   ```bash
   cat .claude/state/current_task.json
   git branch --show-current
   ```

2. **Resume with Claude**
   ```
   You: Let's continue
   
   Claude: [Loads context automatically via SessionStart hook]
           [Shows current task and last work log entry]
           [Presents next steps]
   ```

### During Development

**Discussion Mode (Default)**
- Explore the codebase
- Discuss architecture
- Review existing patterns
- Plan implementation

**Switching to Implementation**
- Say: "go ahead" / "make it so" / "run that"
- Claude can now edit files
- Returns to discussion after changes

**Manual Mode Toggle**
```bash
# Check current mode
daic

# Output: You are now in [Discussion/Implementation] Mode
```

### Ending Your Session

Before context window fills:
```
You: We're getting close to context limit. Please use the logging 
     agent to update the work log, then use context-refinement to
     capture any discoveries.

Claude: [Invokes logging agent to organize work log]
        [Invokes context-refinement to update context manifest]
        
        Session work has been logged and context updated.
```

## Working with Agents

### Context Gathering (Mandatory for New Tasks)

```
You: Use the context-gathering agent to analyze how the payment
     system works and create a context manifest for task m-add-stripe

Claude: I'll use the context-gathering agent to analyze the payment
        system and create a comprehensive context manifest.
        
        [Agent returns detailed context]
        
        The context manifest has been created, documenting the current
        payment architecture, Stripe integration points, and how the
        new feature should connect.
```

### Code Review (Before Commits)

```
You: Use the code-review agent to review the authentication 
     implementation in src/auth/

Claude: I'll have the code-review agent review the authentication
        implementation for security and quality issues.
        
        [Agent returns prioritized feedback]
        
        The review found 2 high-priority issues:
        1. JWT secret is hardcoded (security risk)
        2. No rate limiting on login endpoint
```

### Knowledge Extraction (External APIs)

```
You: I need to integrate with the Stripe Connect API

Claude: I'll use the knowledge-extraction agent to research Stripe
        Connect documentation and create a comprehensive knowledge file.
        
        [Agent researches and returns knowledge file]
        
        The agent has created sessions/knowledge/stripe-connect.md with
        complete API documentation, authentication details, and 
        integration examples.
```

## Context Management

### Understanding Context Windows

The Sessions framework monitors token usage:
- **75% Warning**: Consider wrapping up current work
- **90% Warning**: Immediately save work and prepare fresh context

### Preserving Context Across Windows

1. **Work Logs**: Automatically track what was done
2. **Context Manifests**: Preserve system understanding  
3. **State Files**: Remember current task and mode
4. **Agent Transcripts**: Record detailed analysis

### Starting Fresh Context

```
You: Let's continue

Claude: [SessionStart hook activates]
        [Reads current task: m-add-user-auth]
        [Loads context manifest]
        [Reviews work log]
        
        Resuming work on user authentication. Last entry shows we
        completed the user model and registration. Next step is
        implementing the login endpoint with JWT generation.
```

## Advanced Patterns

### Multi-Repository Coordination

For projects with multiple repositories:

```markdown
---
task: m-add-api-endpoint
branch: feature/new-endpoint
services: [api-service, web-client, shared-types]
---
```

The branch enforcement ensures all repos stay synchronized.

### Parallel Task Exploration

While working on one task, explore another using agents:

```
You: While staying on the current task, use the context-gathering
     agent to explore what would be needed for task m-add-websockets

Claude: I'll use the context-gathering agent to explore the websockets
        task while maintaining our current context on authentication.
        
        [Agent investigates separately]
        
        The agent's analysis is complete. The websockets implementation
        would require... [summary]. The full context has been saved to
        the task file for when we switch to that task.
```

### Complex Refactoring

For large refactors, break into subtasks:

```markdown
# Main task: m-refactor-database

## Subtasks (in work log)
- [x] Analyze current schema
- [x] Design new structure  
- [ ] Create migration plan
- [ ] Implement migrations
- [ ] Update model layer
- [ ] Update API endpoints
- [ ] Test and verify
```

### Emergency Overrides

If hooks malfunction:

```bash
# Force implementation mode
echo '{"mode": "implementation"}' > .claude/state/daic-mode.json

# Clear task state
echo '{"task": null, "branch": null}' > .claude/state/current_task.json

# Disable hooks temporarily
mv .claude/hooks .claude/hooks.disabled
```

## Best Practices

### DO's

✅ **Create task files** before starting work  
✅ **Use context-gathering** for all new tasks  
✅ **Discuss before implementing** (respect D.A.I.C.)  
✅ **Delegate heavy lifting** to agents  
✅ **Update work logs** frequently  
✅ **Review code** before committing  

### DON'Ts

❌ **Skip discussion phase** - It saves time long-term  
❌ **Overload CLAUDE.md** - Keep it under 100 lines  
❌ **Work on multiple tasks** - Context pollution  
❌ **Ignore token warnings** - You'll lose work  
❌ **Research docs yourself** - Use knowledge-extraction  
❌ **Commit without review** - Use code-review agent  

## Tips and Tricks

### Efficient Trigger Phrases

Create your own during setup:
- "ship it" → Implementation mode
- "let's code" → Implementation mode  
- "execute" → Implementation mode

### Quick Context Checks

```bash
# Alias for common checks
alias cs='cat .claude/state/current_task.json'
alias dmode='cat .claude/state/daic-mode.json'
```

### Task Templates

Create domain-specific templates:
```bash
cp sessions/tasks/TEMPLATE.md sessions/tasks/TEMPLATE-api.md
cp sessions/tasks/TEMPLATE.md sessions/tasks/TEMPLATE-frontend.md
# Customize for common task types
```

### Batch Operations

When multiple small changes are needed:
```
You: I need to update all API endpoints to use the new auth middleware.
     Here's the list: [endpoints]. Discuss the approach first.

Claude: [Discusses approach]

You: go ahead with all of them

Claude: [Makes all changes in implementation mode]
```

## Troubleshooting Workflows

### "Claude won't stop discussing"

Check you're using correct trigger phrases:
```bash
# See configured phrases
cat sessions/sessions-config.json | grep trigger_phrases
```

### "Can't find my work"

Work is preserved in multiple places:
```bash
# Current task work log
cat sessions/tasks/$(jq -r .task .claude/state/current_task.json).md

# Agent transcripts  
ls .claude/state/*/
```

### "Context manifest is outdated"

```
You: The context manifest seems outdated. Use the context-refinement
     agent to update it with our recent discoveries about the 
     caching system.

Claude: [Updates context manifest via agent]
```

## API Mode vs Max Mode

### Understanding Token Economics

The Sessions framework actually **SAVES tokens** for most users through:
- **Context persistence**: No need to re-explain tasks across sessions
- **Auto-loading**: Eliminates "what are we working on?" cycles
- **DAIC enforcement**: Prevents wasteful failed implementation attempts
- **Specialized agents**: Work in minimal contexts, return structured results

However, it uses these saved tokens to enable **ultrathink** - Claude's maximum thinking budget - on every interaction for consistently better results.

### When to Use API Mode

**Max Mode (Default):**
- You have a Claude Code Max subscription ($20-200/month)
- Token usage is not a concern
- You want the best possible performance
- Ultrathink is automatically enabled on every message

**API Mode:**
- You're using Claude Code with API keys
- You're budget-conscious about token usage
- You want manual control over thinking budget
- Ultrathink is disabled (but can be triggered with `[[ ultrathink ]]`)

### Configuring API Mode

**During Installation:**
```bash
# You'll be prompted during setup:
Enable API mode? (y/n): y
```

**After Installation:**
```bash
# Use the slash command to toggle
/api-mode

# Or edit directly
jq '.api_mode = true' sessions/sessions-config.json > tmp && mv tmp sessions/sessions-config.json
```

### Manual Ultrathink Control

In API mode, you can still trigger maximum thinking when needed:
```
[[ ultrathink ]]
How should we architect this complex system?
```

### Token Savings Breakdown

| Feature | Tokens Saved | How |
|---------|--------------|-----|
| SessionStart | 200-500/session | Auto-loads task context |
| Context Manifests | 1000-5000/task | Front-loads exploration |
| DAIC Enforcement | 500-2000/task | Prevents wrong implementations |
| Work Logs | 500-1000/session | Maintains continuity |
| Warning Systems | Variable | Prevents context overflow |

**Bottom Line:** Sessions saves more tokens than it uses, even with ultrathink enabled. API mode is for those who want maximum control.

## Getting Help

1. **Check protocols**: `ls sessions/protocols/`
2. **Review agent capabilities**: `ls sessions/agents/`
3. **Examine examples**: Look at completed tasks in `sessions/tasks/done/`
4. **GitHub issues**: Report bugs or request features

Remember: The Sessions framework is about collaborative excellence, not restriction. Embrace the discussion phase - it's where the best solutions emerge.