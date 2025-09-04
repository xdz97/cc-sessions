---
allowed-tools: Bash(python3:*), Bash(python:*)
argument-hint: "trigger phrase"
description: Add a new trigger phrase for task completion protocol
---

!`python3 sessions/scripts/add_phrases.py complete "$ARGUMENTS" 2>/dev/null || python sessions/scripts/add_phrases.py complete "$ARGUMENTS"`

Tell the user: "You have successfully added '$ARGUMENTS' as a trigger phrase for task completion. When you say this phrase, Claude will follow the task completion protocol to wrap up the current task cleanly."