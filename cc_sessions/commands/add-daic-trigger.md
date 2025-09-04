---
allowed-tools: Bash(python3:*), Bash(python:*)
argument-hint: "trigger phrase"
description: Add a new trigger phrase for switching to implementation mode
---

!`python3 sessions/scripts/add_phrases.py daic "$ARGUMENTS" 2>/dev/null || python sessions/scripts/add_phrases.py daic "$ARGUMENTS"`

Tell the user: "You have successfully added '$ARGUMENTS' as a trigger phrase for switching to implementation mode. When you say this phrase, Claude will exit discussion mode and begin implementing code based on the discussed approach."