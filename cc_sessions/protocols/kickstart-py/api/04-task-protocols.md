# Task Protocols

cc-sessions organizes all work with tasks - markdown files that track what you're building, success criteria, and work logs.

## Three Main Protocols

**1. Task Creation** - Record work when you discover it
- Creates task file with structure
- System default: **mek:**
- Example: `mek: fix login redirect loop`

**2. Task Startup** - Begin work with context loaded
- Loads task, creates/checks out branch, sets up tracking
- System default: **start^:**
- Example: `start^: @h-fix-auth-redirect.md`

**3. Task Completion** - Finish and merge to main
- Runs quality checks, commits, merges
- System default: **finito**

## Git Branch Integration

Every task maps to a git branch - no accidental commits to main.

## Configure Your Trigger Phrases

### Task Creation Phrase

System default: **mek:**

Pick something natural for describing new work.

Good examples: "new task:", "create task:", "work on:"
Bad examples: "make" (too common), "do" (too vague)

Your phrase:

[Wait for response]

Run: `/sessions config triggers add create <your phrase>`

### Task Startup Phrase

System default: **start^:**

Pick something natural for beginning work.

Good examples: "begin task:", "work on:", "lets start:"
Bad examples: "start" (too common)

Your phrase:

[Wait for response]

Run: `/sessions config triggers add start <your phrase>`

### Task Completion Phrase

System default: **finito**

Pick something natural for finishing work.

Good examples: "done", "complete", "ship it"
Bad examples: "finished" (too common in conversation)

Your phrase:

[Wait for response]

Run: `/sessions config triggers add complete <your phrase>`

### Confirm Configuration

Run: `python -m sessions.api config triggers list`

Shows all your configured phrases.

---

Run: `python -m sessions.kickstart next`
