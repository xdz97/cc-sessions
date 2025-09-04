---
allowed-tools: Bash(python3:*), Bash(python:*)
argument-hint: "trigger phrase"
description: Add a new trigger phrase for context compaction protocol
---

!`python3 sessions/scripts/add_phrases.py compact "$ARGUMENTS" 2>/dev/null || python sessions/scripts/add_phrases.py compact "$ARGUMENTS"`

Tell the user: "You have successfully added '$ARGUMENTS' as a trigger phrase for context compaction. When you say this phrase, Claude will follow the context compaction protocol to consolidate work and clear the context window."