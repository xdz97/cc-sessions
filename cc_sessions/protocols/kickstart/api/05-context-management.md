# Context Management

cc-sessions tracks your token usage and helps you manage context windows.

## Two Ways to Reset Context

**Compaction** - When you have an active task and run out of tokens
- Preserves task state, todos, work logs
- Runs maintenance agents to update documentation
- Task continues in fresh window
- System default: **squish**

**/clear** - When you have no active task
- Simple context reset
- Use after completing tasks
- Built-in Claude Code command

## When Compaction Happens

cc-sessions watches token usage:
- **85% full** - Warning appears, keep going
- **90% full** - Hard recommendation to compact

**Most tasks shouldn't need compaction.** You only compact if you're mid-task and running out of space.

## Set Up Compaction Trigger

System default: **squish**

Pick something natural for running out of space.

Good examples: "lets compact", "compress"
Bad examples: "save" (too vague), "clear" (confusing)

Your phrase:

[Wait for response]

Run: `/sessions config triggers add compact <your phrase>`

Confirm it was added.

## The Rule

- **Active task, running out of tokens?** Use compaction
- **No active task?** Use /clear

---

Run: `python -m sessions.kickstart next`
