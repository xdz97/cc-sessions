# Agent Customization

Welcome back! Your kickstart task carried forward perfectly across the compaction.

Now let's talk about one of cc-sessions' most powerful features: **customizable agents**.

## What You've Seen So Far

The **context-gathering agent** ran during your kickstart task startup to analyze your repo and provide configuration recommendations. You were also offered the option to run it when creating your first real task - it can run at either task creation or startup.

The **compaction protocol** runs three maintenance agents:
- **logging** - Consolidates your work logs chronologically in the task file
- **context-refinement** - Checks if you discovered anything important that should update the context manifest
- **service-documentation** - Updates CLAUDE.md files if service interfaces changed

That's 4 of the 5 specialized agents. The fifth is **code-review**, which runs before commits when you've written significant code.

## Customizing Agent Behavior

Agent prompts can be customized based on your repo and preferences. Instead of generic instructions, agents can know:
- What patterns matter in your codebase
- What security concerns apply to your domain
- What performance standards you care about

## Which Agents Should You Customize?

For most users, two agents are worth customizing:

**1. context-gathering** - Runs when creating or starting tasks
- Should know your architectural patterns
- Should understand your database and API conventions
- Should look for framework-specific patterns

**2. code-review** - Runs before committing code
- Should know who uses your software and how
- Should understand performance requirements
- Should check domain-specific concerns

The other three agents work well without customization. You can adjust them later if needed.

## Customize Context-Gathering

The repository detection already found your tech stack. Now let's talk about the patterns your codebase follows.

**What patterns does your codebase follow?**

Think about:
- Service structure: Microservices, modules, packages?
- Database patterns: Redis key formats, Postgres schemas, ORM usage?
- API conventions: REST endpoints, auth flows, routing patterns?

[Wait for user's response]

---

**Instructions after user describes patterns:**

Have a conversational exchange to understand their patterns. Scan the codebase together to identify examples of what they're describing.

After gathering pattern info:

1. Read the package agent: `.claude/agents/context-gathering.md`
2. Update the agent so that it:
   - Keeps the core structure and instructions
   - Adds sections for their specific patterns (service structure, database conventions, API patterns)
   - Includes framework-specific pattern examples from their codebase

3. Show them a snippet of what you added and confirm it looks right

---

**After context-gathering customization:**

Run: `python -m sessions.kickstart next`

This will move to code-review customization.
