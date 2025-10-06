# Tasks and Branches: The Second Core System

You've learned about DAIC enforcement - how cc-sessions keeps you in control during implementation. Now let's talk about the second important system: **tasks and branches**.

## The Task System

cc-sessions uses a **task system** to organize all your work. Each task is a markdown file that tracks:
- What you're building or fixing
- Success criteria (what "done" looks like)
- Context about the codebase
- Work logs across sessions
- Git branch information

## Git Branch Integration

Every task maps to a git branch. This means:
- No accidental commits to main
- Clean separation of work
- Easy context switching between tasks
- Foolproof source control

## Four Protocols for Task Workflow

The task system has four main protocols:

1. **Task Creation** - Record work when you discover it
2. **Task Startup** - Start work with full context loaded
3. **Context Compaction** - Carry work across multiple context windows when you hit token limits
4. **Task Completion** - Complete work and merge to main when done

Each protocol is triggered by a phrase, guides you through the workflow, and ensures nothing falls through the cracks.

## Let's Start with Task Creation

We're going to walk you through creating your first task. The default trigger phrase for task creation is:

**mek:** <task description>

Example: `mek: we need to refactor user and staff models to support presave method calling on child classes so our specialized user types can add logic before saving to cache`

## Add Your Own Task Creation Phrase

You can add your own trigger phrase for task creation. Pick something that feels natural when you're describing new work.

Good examples: "new task:", "create task:", "work on:", "task:"
Bad examples: "make" (too common), "do" (too vague)

What phrase would you like to use for creating tasks?

[Wait for user's response]

---

**Instructions after user provides their phrase:**

Tell them to add it using the `/sessions` command:

```
/sessions config triggers add create <user's phrase>
```

Example: `/sessions config triggers add create new task:`

Tell them to run it now.

[Wait for them to run the command]

---

**After they run the command:**

Confirm their phrase has been added.

Run: `python -m sessions.kickstart next`

This will guide them through actually creating a task.
