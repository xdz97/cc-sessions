# Advanced Concepts

These aren't essential for day-to-day work, but useful when you need them.

## Bypass Mode

Temporarily disable DAIC enforcement for rapid pair programming.

**Only you can activate it:**
```bash
/sessions state mode bypass
```

In bypass mode:
- Edit/Write tools work in discussion mode without approval
- TodoWrite exact-match enforcement disabled
- All DAIC constraints removed
- Either of us can deactivate (returning to safety always allowed)

**Use sparingly** - it removes all safeties. Toggle off with same command.

## Directory Tasks

For complex multi-phase work with multiple subtasks.

**The task creation protocol will ask if you want a directory structure** when your description suggests multiple phases. You'll see this option automatically - you don't need to remember to request it.

Directory tasks:
- Create directory with README.md and subtask files
- Work through subtasks one by one
- Stay on same branch until everything's done

## Task Index System

Organize tasks by domain/feature/system:

```
sessions/tasks/
├── frontend/
├── backend/
└── bugs/
```

**During task creation, I'll ask if you want to update an index.** If you've set up indexes, you can categorize tasks. If not, just skip it.

View indexed tasks:
```bash
/sessions tasks idx list          # Show all indexes
/sessions tasks idx frontend      # Show frontend tasks
```

## Stashed Todos

Active todos auto-stash during compaction or task creation. They restore when the protocol completes.

View: `/sessions state todos`

## The /sessions Command

Your control panel for everything.

**Main categories:**

**1. /sessions config** - Configuration management
```
triggers, git, env, features, read, write, tools
```

**2. /sessions state** - Inspect current state
```
mode, task, todos
```

**3. /sessions tasks** - Task management
```
idx list, idx <name>, start @<task>
```

**Smart help system:**
- `/sessions help` - Top-level help
- `/sessions config` - Config help
- `/sessions config trigger` - Trigger commands help
- Wrong commands show what's valid and guide you

You can typo, use partial commands, forget arguments - it'll tell you what's valid.

---

**Questions about any of these features?**

[Wait for response]

If no questions: Run `python -m sessions.kickstart next`
