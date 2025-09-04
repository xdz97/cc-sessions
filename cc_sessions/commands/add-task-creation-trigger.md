---
allowed-tools: Bash(python3:*), Bash(python:*)
argument-hint: "trigger phrase"
description: Add a new trigger phrase for task creation protocol
---

!`python3 sessions/scripts/add_phrases.py create "$ARGUMENTS" 2>/dev/null || python sessions/scripts/add_phrases.py create "$ARGUMENTS"`

Tell the user: "You have successfully added '$ARGUMENTS' as a trigger phrase for task creation. When you say this phrase, Claude will follow the task creation protocol to help you define and set up a new task."