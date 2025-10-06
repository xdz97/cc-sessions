# Advanced Features

You've learned the core workflow, configured your setup, and customized agents. Now let's cover some power features you might need later.

These aren't essential for day-to-day work, but they're useful when you need them. I'll walk through each one - let me know if anything doesn't make sense.

## Bypass Mode

Sometimes you need to temporarily disable DAIC enforcement. Like when you're pair programming and want rapid iteration without the "approve implementation" step.

**Only you can activate bypass mode** - I can't turn it on myself. You enable it with:
```bash
/sessions state mode bypass
```

Or directly: `python -m sessions.api state mode bypass`

In bypass mode:
- I can use Edit/Write tools in discussion mode without waiting for approval
- TodoWrite exact-match enforcement is disabled (I can change todo lists mid-implementation)
- sessions-state.json protection is disabled (direct editing allowed)
- All DAIC behavioral constraints are removed
- Either of us can deactivate it (returning to safety is always allowed)

To deactivate, run `/sessions state mode bypass` again to toggle it off.

**Use it extremely sparingly** - bypass mode removes all the safeties DAIC provides. It's for rapid pair programming sessions where you want full control and are actively watching what happens. In many cases, you can get similar work done by using cc-sessions without an active task loaded. This is more of an escape hatch if the system goes haywire.

Make sense? Any questions about bypass mode?

[Wait for user's response]

---

**After they respond:**

If they have questions, answer them. When ready to continue, move to the next section.

## Directory Tasks

Most tasks are simple files. But sometimes you have complex multi-phase work that needs multiple subtasks.

Directory tasks let you:
- Create a task directory with README.md and subtask files
- Work through subtasks one by one
- Stay on the same feature branch until everything's done
- Merge only when the entire effort completes

When creating a task, the protocol asks if you want a directory structure. Say yes when:
- The work has 3+ distinct phases
- You need clear separation between subtasks
- You want to plan the whole effort upfront

Got it? Any questions about directory tasks?

[Wait for user's response]

---

**After they respond:**

If they have questions, answer them. When ready to continue, move to the next section.

## Task Index System

If you have lots of tasks, you can organize them into indexes by features, code paths, submodules, systems (i.e. auth, user-model, caching, etc.) - however you want really:

```
sessions/tasks/
├── frontend/
├── backend/
├── infrastructure/
└── bugs/
```

The task creation protocol asks if you want to update indexes. You can track tasks by area and list them separately:

```bash
/sessions tasks idx list          # Show all indexes
/sessions tasks idx frontend      # Show frontend tasks
```

Clear on task indexes?

[Wait for user's response]

---

**After they respond:**

If they have questions, answer them. When ready to continue, move to the next section.

## Stashed Todos

When you run context compaction or task creation, any active todos get stashed automatically. When the new session starts or when the task creation protocol is complete, they're restored.

You can also manually manage stashed todos:
```bash
/sessions state todos             # View active and stashed
```

Stashed todos survive across sessions until you complete them or manually clear them.

Make sense?

[Wait for user's response]

---

**After they respond:**

If they have questions, answer them. When ready to continue, move to the next section.

## The /sessions Slash Command

You've used `/sessions config` during kickstart. The `/sessions` slash command is your control panel for everything.

It has **four main categories:**

**1. /sessions config** - Manage your configuration
```
/sessions config                          # Show everything
/sessions config triggers                 # Trigger phrase management
/sessions config git                      # Git preferences
/sessions config env                      # Environment settings
/sessions config features                 # Feature toggles
/sessions config read                     # Bash read patterns
/sessions config write                    # Bash write patterns
/sessions config tools                    # Tool blocking settings
```

**2. /sessions state** - Inspect current state
```
/sessions state                           # Full state overview
/sessions state mode                      # Current mode (discussion/implementation/bypass)
/sessions state task                      # Current task details
/sessions state todos                     # Active and stashed todos
```

**3. /sessions tasks** - Task management
```
/sessions tasks idx list                  # List all task indexes
/sessions tasks idx <name>                # Show tasks in specific index
/sessions tasks start @<task-name>        # Start a task with validation
```

### The Smart Help System

Here's the cool part: **you can't really break it.**

**Multi-level help:**
- `/sessions` or `/sessions help` - Top-level help with all subsystems
- `/sessions config` - Config subsystem help
- `/sessions config trigger` - Trigger commands help
- `/sessions state` - State subsystem help
- `/sessions tasks` - Task commands help

**When you mess up, it guides you:**
- `/sessions blah` → "Unknown subsystem: blah. Valid subsystems: tasks, state, config"
- `/sessions config wat` → "Unknown command: wat" + shows you all config commands
- `/sessions config trigger add` (missing args) → Shows you the format and what arguments you need
- `/sessions config trigger add go unknown` → "Invalid category 'unknown'. Valid: go, no, create, start, complete, compact"

The help system is **command-aware**. It knows where you are in the command tree and shows you exactly what went wrong and what's valid at that level.

You can typo stuff, give partial commands, forget arguments - it'll always tell you what's valid and point you to the right help.

Make sense? Feel free to mess around with `/sessions` commands to see how it works - just say "continue" when you're ready

[Wait for user's response]

---

**After they respond:**

If they have questions, answer them. When ready to continue:

**That's it for advanced features.** These are all optional. Use them when you need them, ignore them when you don't.

Ready to wrap up kickstart?

Run: `python -m sessions.kickstart next`

This will move to graduation.
