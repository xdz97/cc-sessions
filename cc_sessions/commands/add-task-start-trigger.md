---
allowed-tools: Bash(python3:*), Bash(python:*)
argument-hint: "trigger phrase"
description: Add a new trigger phrase for starting a task
---

!`python3 sessions/scripts/add_phrases.py start "$ARGUMENTS" 2>/dev/null || python sessions/scripts/add_phrases.py start "$ARGUMENTS"`

Tell the user: "You have successfully added '$ARGUMENTS' as a trigger phrase for starting a task. When you say this phrase, Claude will follow the task startup protocol to initialize work on the specified task."